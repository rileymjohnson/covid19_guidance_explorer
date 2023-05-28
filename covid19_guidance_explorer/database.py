from playhouse.postgres_ext import (
    PostgresqlExtDatabase,
    Model,
    CharField,
    TextField,
    ForeignKeyField,
    DateTimeField,
    BooleanField,
    SmallIntegerField,
    BinaryJSONField,
    TSVectorField,
    Expression,
    TS_MATCH,
    JOIN,
    fn
)


from typing import Optional, Generator
from datetime import datetime
from pathlib import Path

from covid19_guidance_explorer.config import config
from covid19_guidance_explorer.utils import (
    random_color,
    PeeweeHelpers,
    file_to_url
)


database = PostgresqlExtDatabase(
    database=config['postgres']['database'],
    user=config['postgres']['user'],
    password=config['postgres']['password']
)
database.connect()

class BaseModel(Model):
    created = DateTimeField(default=datetime.now)

    class Meta:
        database = database

    @classmethod
    def get_num_unique_records(cls: Model) -> int:
        cursor = database.execute_sql(f"""
        SELECT
        COUNT(DISTINCT "t1"."id")
        from
        "{cls._meta.table_name}" as "t1"
        """)

        return cursor.fetchone()[0]

    @staticmethod
    def preprocess(instance: Model) -> Model:
        return instance

    @classmethod
    def get_values(
        cls,
        *,
        k: Optional[int]=None,
        n: Optional[int]=None,
        search_string: Optional[str]=None,
        quick_search: Optional[bool]=False
    ) -> Generator:
        selector = cls._selector()

        if search_string is not None:
            if quick_search:
                search_field = cls.quick_search_content
            else:
                search_field = cls.search_content

            search_expression = Expression(
                search_field,
                TS_MATCH,
                fn.websearch_to_tsquery(
                    'english',
                    search_string
                )
            )

            selector = selector.where(search_expression)

        if k is not None and n is not None:
            selector = selector.paginate(k, n)

        for instance in selector:
            yield cls.preprocess(instance)

    @classmethod
    def get_num_pages(
        cls,
        n: int,
        search_string: Optional[str]=None,
        quick_search: Optional[bool]=False
    ) -> int:
        selector = cls.select(
            fn.CEIL(fn.COUNT(cls.id) / float(n))
        )

        if search_string is not None:
            if quick_search:
                search_field = cls.quick_search_content
            else:
                search_field = cls.search_content

            search_expression = Expression(
                search_field,
                TS_MATCH,
                fn.websearch_to_tsquery(
                    'english',
                    search_string
                )
            )

            selector = selector.where(search_expression)

        return int(selector.scalar())

    @classmethod
    def get_one(cls, id: int) -> Model:
        instance = cls \
            ._selector() \
            .where(cls.id == id) \
            .first()

        return cls.preprocess(instance)

class FileType(BaseModel):
    mimetype = CharField()
    suffix = CharField()
    label = CharField()

    @classmethod
    def get_select_values(cls):
        select_values = cls \
            .select(
                cls.label,
                cls.id.alias('value')
            ) \
            .order_by(cls.label) \
            .dicts()

        return list(select_values)

class Language(BaseModel):
    label = CharField()
    value = CharField()

    @classmethod
    def get_select_values(cls):
        select_values = cls \
            .select(
                cls.label,
                cls.id.alias('value')
            ) \
            .order_by(cls.label) \
            .dicts()

        return list(select_values)

class Tag(BaseModel):
    text = CharField()
    color = CharField(default=random_color)
    search_content = TSVectorField()

    @classmethod
    def get_select_values(cls):
        select_values = cls \
            .select(
                cls.text.alias('label'),
                cls.id.alias('value')
            ) \
            .order_by(cls.text) \
            .dicts()

        return list(select_values)

    @classmethod
    def _selector(cls):
        return cls \
            .select(
                *PeeweeHelpers.all_but(cls, [cls.search_content])
            )

class Jurisdiction(BaseModel):
    label = CharField()
    value = CharField()
    search_content = TSVectorField()

    @classmethod
    def get_select_values(cls):
        select_values = cls \
            .select(
                cls.label,
                cls.id.alias('value')
            ) \
            .order_by(cls.label) \
            .dicts()

        return list(select_values)

    @classmethod
    def _selector(cls):
        return cls \
            .select(
                *PeeweeHelpers.all_but(cls, [cls.search_content])
            ) \
            .order_by(cls.label)

class DocumentType(BaseModel):
    label = CharField()
    value = CharField()
    search_content = TSVectorField()

    @classmethod
    def get_select_values(cls):
        select_values = cls \
            .select(
                cls.label,
                cls.id.alias('value')
            ) \
            .order_by(cls.label) \
            .dicts()

        return list(select_values)

    @classmethod
    def _selector(cls):
        return cls \
            .select(
                *PeeweeHelpers.all_but(cls, [cls.search_content])
            )

class DocumentIssuer(BaseModel):
    long_name = TextField()
    short_name = CharField()
    search_content = TSVectorField()

    @property
    def icon_url(self) -> str:
        file = Path(config['paths']['issuer_icons_dir']) \
            .joinpath(f'{self.id}.png') \
            .as_posix()

        return file_to_url(file)

    @classmethod
    def _selector(cls):
        num_document_versions = cls \
            .select(
                cls.id,
                fn.COUNT(DocumentVersion.id).alias('_')
            ) \
            .join(Document, join_type=JOIN.LEFT_OUTER) \
            .join(DocumentVersion, join_type=JOIN.LEFT_OUTER) \
            .group_by(cls) \
            .alias('_')

        num_documents = cls \
            .select(
                cls.id,
                fn.COUNT(Document.id).alias('_')
            ) \
            .join(Document, join_type=JOIN.LEFT_OUTER) \
            .group_by(cls)

        return cls \
            .select(
                *PeeweeHelpers.all_but(cls, [cls.search_content]),
                num_documents.c._.alias('num_documents'),
                num_document_versions.c._.alias('num_document_versions')
            ) \
            .join(num_documents, on=(cls.id == num_documents.c.id)) \
            .switch(cls) \
            .join(num_document_versions, on=(cls.id == num_document_versions.c.id)) \
            .objects()

class Document(BaseModel):
    title = TextField()
    slug = TextField()
    issuer = ForeignKeyField(DocumentIssuer, backref='documents')
    language = ForeignKeyField(Language, null=True)
    file_type = ForeignKeyField(FileType, null=True)
    source = TextField()
    source_notes = TextField(null=True)
    reviewed = BooleanField(default=False)
    flagged_for_review = BooleanField(default=False)
    has_relevant_information = BooleanField(null=True)
    is_foreign_language = BooleanField(null=True)
    is_malformed = BooleanField(null=True)
    is_empty = BooleanField(null=True)
    importance = SmallIntegerField(null=True)
    notes = TextField(null=True)
    variables = BinaryJSONField(default=lambda: {})
    search_content = TSVectorField()
    review_checklist = BinaryJSONField(default=lambda: {})

    @staticmethod
    def preprocess(instance: Model) -> Model:
        if hasattr(instance, 'versions'):
            for version in instance.versions:
                version['effective_date'] = datetime.fromisoformat(
                    version['effective_date']
                )

                if version['termination_date'] is not None:
                    version['termination_date'] = datetime.fromisoformat(
                        version['termination_date']
                    )

        if instance.tags is None:
            instance.tags = []

        if instance.types is None:
            instance.types = []

        if instance.jurisdictions is None:
            instance.jurisdictions = []

        return instance

    @classmethod
    def _selector(cls):
        alias_effective_date = DocumentVersion.alias()
        alias_termination_date = DocumentVersion.alias()

        document_types = DocumentType \
            .select(
                cls.id,
                fn.JSON_AGG(DocumentType).alias('_')
            ) \
            .join(DocumentDocumentTypeThroughTable) \
            .join(cls) \
            .group_by(cls.id) \
            .alias('types')

        document_jurisdictions = Jurisdiction \
            .select(
                cls.id,
                fn.JSON_AGG(Jurisdiction).alias('_')
            ) \
            .join(DocumentJurisdictionThroughTable) \
            .join(cls) \
            .group_by(cls.id) \
            .alias('jurisdictions')

        document_tags = Tag \
            .select(
                cls.id,
                fn.JSON_AGG(Tag).alias('_')
            ) \
            .join(DocumentTagThroughTable) \
            .join(cls) \
            .group_by(cls.id) \
            .alias('tags')

        document_versions_nums = DocumentVersion \
            .select(
                DocumentVersion.id,
                fn \
                    .RANK() \
                    .over(
                        order_by=[DocumentVersion.effective_date],
                        partition_by=[cls.id]
                    ) \
                    .alias('_')
            ) \
            .join(cls) \
            .group_by(cls.id, DocumentVersion.id) \
            .alias('document_versions_nums')

        document_versions = DocumentVersion \
            .select(
                cls.id,
                fn.COUNT(DocumentVersion.id).alias('__'),
                fn.JSON_AGG(
                    fn.JSON_BUILD_OBJECT(
                        'id', DocumentVersion.id,
                        'title', DocumentVersion.title,
                        'slug', DocumentVersion.slug,
                        'effective_date', DocumentVersion.effective_date,
                        'termination_date', DocumentVersion.termination_date,
                        'source', DocumentVersion.source,
                        'version_num', document_versions_nums.c._
                    )
                ).alias('_')
            ) \
            .join(document_versions_nums, on=(DocumentVersion.id == document_versions_nums.c.id)) \
            .join_from(DocumentVersion, cls) \
            .group_by(cls.id) \
            .alias('document_versions')

        effective_date = cls \
            .select(
                cls.id,
                fn.MIN(alias_effective_date.effective_date).alias('_')
            ) \
            .join(alias_effective_date) \
            .group_by(cls.id) \
            .alias('effective_date')

        termination_date = cls \
            .select(
                cls.id,
                fn.MIN(alias_termination_date.termination_date).alias('_')
            ) \
            .join(alias_termination_date) \
            .group_by(cls.id) \
            .alias('termination_date')

        return cls \
            .select(
                *PeeweeHelpers.all_but(cls, cls.search_content),
                document_types.c._.alias('types'),
                document_jurisdictions.c._.alias('jurisdictions'),
                document_tags.c._.alias('tags'),
                document_versions.c._.alias('versions'),
                document_versions.c.__.alias('num_versions'),
                effective_date.c._.alias('effective_date'),
                termination_date.c._.alias('termination_date')
            ) \
            .join(
                document_types,
                on=(cls.id == document_types.c.id),
                join_type=JOIN.LEFT_OUTER
            ) \
            .join(
                document_jurisdictions,
                on=(cls.id == document_jurisdictions.c.id),
                join_type=JOIN.LEFT_OUTER
            ) \
            .join(
                document_tags,
                on=(cls.id == document_tags.c.id),
                join_type=JOIN.LEFT_OUTER
            ) \
            .join(document_versions, on=(cls.id == document_versions.c.id)) \
            .join(effective_date, on=(cls.id == effective_date.c.id)) \
            .join(termination_date, on=(cls.id == termination_date.c.id)) \
            .order_by(cls.slug) \
            .objects()

class DocumentVersion(BaseModel):
    title = TextField()
    slug = TextField()
    document = ForeignKeyField(Document, backref='versions')
    effective_date = DateTimeField()
    termination_date = DateTimeField(null=True)
    source = TextField()
    source_notes = TextField(null=True)
    content = TextField()
    language = ForeignKeyField(Language, null=True)
    file_type = ForeignKeyField(FileType, null=True)
    reviewed = BooleanField(default=False)
    flagged_for_review = BooleanField(default=False)
    has_relevant_information = BooleanField(null=True)
    is_foreign_language = BooleanField(null=True)
    is_malformed = BooleanField(null=True)
    is_empty = BooleanField(null=True)
    is_terminating_version = BooleanField(null=True)
    importance = SmallIntegerField(null=True)
    notes = TextField(null=True)
    variables = BinaryJSONField(default=lambda: {})
    search_content = TSVectorField()
    quick_search_content = TSVectorField(null=True)
    review_checklist = BinaryJSONField(default=lambda: {})
    file_hash = CharField(max_length=64)
    content_hash = CharField(max_length=64)
    highlights = BinaryJSONField(default=lambda: {})

    @property
    def file(self) -> str:
        if self.file_type is None:
            return None

        file_name = f'{self.id}{self.file_type.suffix}'

        return Path(config['paths']['files_dir']) \
            .joinpath(file_name) \
            .as_posix()

    @property
    def processed_file(self) -> str:
        if self.file_type is None:
            return None

        file_name = f'{self.id}{self.file_type.suffix}'

        return Path(config['paths']['processed_files_dir']) \
            .joinpath(file_name) \
            .as_posix()

    @property
    def processed_file_exists(self) -> bool:
        processed_file = self.processed_file

        return processed_file is not None and \
            Path(processed_file).exists()

    @property
    def presentation_ready_file(self) -> str:
        if self.processed_file_exists:
            return self.processed_file
        else:
            return self.file

    @property
    def thumbnail_file(self) -> str:
        return Path(
            config['paths']['document_versions_thumbnails_dir']
        ) \
            .joinpath(f'{self.id}.png') \
            .as_posix()

    @property
    def icon_url(self) -> str:
        return file_to_url(self.thumbnail_file)

    @classmethod
    def _selector(cls):
        document_version_tags = cls \
            .select(
                fn.JSON_AGG(Tag).alias('tags'),
                cls.id
            ) \
            .join(DocumentVersionTagThroughTable) \
            .join(Tag) \
            .group_by(cls.id) \
            .alias('tags')

        document_version_types = cls \
            .select(
                fn.JSON_AGG(DocumentType).alias('types'),
                cls.id
            ) \
            .join(DocumentVersionDocumentTypeThroughTable) \
            .join(DocumentType) \
            .group_by(cls.id) \
            .alias('types')

        document_version_jurisdictions = cls \
            .select(
                fn.JSON_AGG(Jurisdiction).alias('jurisdictions'),
                cls.id
            ) \
            .join(DocumentVersionJurisdictionThroughTable) \
            .join(Jurisdiction) \
            .group_by(cls.id) \
            .alias('jurisdictions')

        document_version_num = cls \
            .select(
                cls.id,
                fn \
                    .RANK() \
                    .over(
                        order_by=[cls.effective_date],
                        partition_by=[Document.id]
                    ) \
                    .alias('version_num')
            ) \
            .join(Document) \
            .alias('version_num')


        document_num_versions = cls \
            .select(
                cls.id,
                fn.COUNT(Document.id).alias('num_versions')
            ) \
            .join(Document) \
            .join(cls.alias('_')) \
            .group_by(cls)

        return cls \
            .select(
                *PeeweeHelpers.all_but(cls, [
                    cls.content,
                    cls.search_content,
                    cls.quick_search_content
                ]),
                fn.ROW_TO_JSON(DocumentIssuer).alias('issuer'),
                fn.TO_JSON(document_version_tags.c.tags).alias('tags'),
                fn.TO_JSON(document_version_jurisdictions.c.jurisdictions).alias('jurisdictions'),
                fn.TO_JSON(document_version_types.c.types).alias('types'),
                fn.TO_JSON(document_version_num.c.version_num).alias('version_num'),
                document_num_versions.c.num_versions.alias('num_versions')
            ) \
            .join(Document) \
            .join(DocumentIssuer) \
            .join(document_version_tags, JOIN['LEFT_OUTER'], on=(cls.id == document_version_tags.c.id)) \
            .join(document_version_jurisdictions, JOIN['LEFT_OUTER'], on=(cls.id == document_version_jurisdictions.c.id)) \
            .join(document_version_types, JOIN['LEFT_OUTER'], on=(cls.id == document_version_types.c.id)) \
            .join(document_version_num, on=(cls.id == document_version_num.c.id)) \
            .join(document_num_versions, on=(cls.id == document_num_versions.c.id)) \
            .order_by(cls.slug, cls.effective_date) \
            .objects()

class DocumentDocumentTypeThroughTable(BaseModel):
    document_type = ForeignKeyField(DocumentType)
    document = ForeignKeyField(Document)

class DocumentTagThroughTable(BaseModel):
    document = ForeignKeyField(Document)
    tag = ForeignKeyField(Tag)

class DocumentJurisdictionThroughTable(BaseModel):
    jurisdiction = ForeignKeyField(Jurisdiction)
    document = ForeignKeyField(Document)

class DocumentVersionDocumentTypeThroughTable(BaseModel):
    document_type = ForeignKeyField(DocumentType)
    document_version = ForeignKeyField(DocumentVersion)

class DocumentVersionTagThroughTable(BaseModel):
    document_version = ForeignKeyField(DocumentVersion)
    tag = ForeignKeyField(Tag)

class DocumentVersionJurisdictionThroughTable(BaseModel):
    jurisdiction = ForeignKeyField(Jurisdiction)
    document_version = ForeignKeyField(DocumentVersion)

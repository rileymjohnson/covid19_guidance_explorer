from jinja2 import Environment, select_autoescape, FileSystemLoader
from typing import Optional, Literal
from collections import Counter
from datetime import datetime
from itertools import groupby
from pathlib import Path
from uuid import uuid4
import pandas as pd
import fitz

from covid19app.database import Document, DocumentVersion
from covid19app.search import search
from covid19app.config import config
from covid19app.utils import (
    insert_html_as_pdf,
    base64_encode_file,
    clean_headline,
    insert_text_into_pdf_page
)


_search_results_report_colors = [
    ('info', 'black'),
    ('warning', 'black'),
    ('primary', 'white'),
    ('success', 'white'),
    ('danger', 'white')
]

def generate_search_results_pdf_report(
    search_string: str,
    *,
    search_mode: Literal[
        'phrase', 'simple', 'plain',
        'normal', 'string', 'regex'
    ] = 'normal',
    case_sensitive: Optional[bool]=False
) -> Path:
    save_file = Path(config['paths']['temp_dir']) \
        .joinpath(f'{uuid4()}.pdf')

    jinja_loader = FileSystemLoader(
        config['paths']['templates_dir'],
        encoding='utf-8'
    )

    jinja_env = Environment(
        loader=jinja_loader,
        autoescape=select_autoescape()
    )

    search_results = search(
        search_string=search_string,
        search_mode=search_mode,
        case_sensitive=case_sensitive,
    )

    search_results = groupby(
        search_results,
        lambda r: r['document_id']
    )

    documents = []

    for i, (document_id, group) in enumerate(search_results):
        document_versions = []

        for j, version in enumerate(group):
            version['effective_date'] = version['effective_date'] \
                .strftime('%Y-%m-%d')

            if version['termination_date'] is None:
                version['termination_date'] = 'N/A'
            else:
                version['termination_date'] = version['termination_date'] \
                    .strftime('%Y-%m-%d')

            if version['headline'] == '':
                version['headline'] = '<strong class="error">No Headline</strong>'
            else:
                version['headline'] = version['headline'].replace('\n', '<br/>')

            version['headline'] = clean_headline(version['headline'])

            version['version_num'] = j + 1

            document_versions.append(version)

        effective_date = min(r['effective_date'] for r in document_versions)
        termination_date = max(r['effective_date'] for r in document_versions)

        title = Counter(
            r['title'] for r in document_versions
        ).most_common(1)[0][0]

        slug = Counter(
            r['slug'] for r in document_versions
        ).most_common(1)[0][0]

        color = _search_results_report_colors[
            i % len(_search_results_report_colors)
        ]

        combined_versions = []

        for group, group_versions in groupby(
            document_versions,
            key=lambda v: (
                v['title'], v['slug'], v['headline']
            )
        ):
            title, slug, headline = group

            group_versions = list(group_versions)

            effective_date = min(
                v['effective_date'] for v in group_versions
            )

            termination_date = max(
                v['termination_date'] for v in group_versions
            )

            start_version = min(r['version_num'] for r in group_versions)
            end_version = max(r['version_num'] for r in group_versions)

            if start_version == end_version:
                version_num = start_version
            else:
                version_num = f'{start_version}-{end_version}'

            combined_versions.append({
                'title': title,
                'slug': slug,
                'headline': headline,
                'effective_date': effective_date,
                'termination_date': termination_date,
                'version_num': version_num
            })

        documents.append({
            'effective_date': effective_date,
            'termination_date': termination_date,
            'document_id': document_id,
            'title': title,
            'slug': slug,
            'versions': combined_versions,
            'document_num': i + 1,
            'num_versions': len(document_versions),
            'color': color
        })

    num_documents = Document.get_num_unique_records()
    num_versions = DocumentVersion.get_num_unique_records()

    num_document_matches = len(documents)
    num_version_matches = sum(len(d['versions']) for d in documents)

    percent_document_matches = num_document_matches / num_documents
    percent_version_matches = num_version_matches / num_versions

    now = datetime.now().strftime('%c')

    icon_date_url = base64_encode_file(config['paths']['icon_file'])

    template = jinja_env \
        .get_template('search_results_info.html')

    cover_page_html = template.render(
        search_string=search_string,
        search_mode=search_mode,
        case_sensitive=case_sensitive,
        num_documents=num_documents,
        num_versions=num_versions,
        num_document_matches=num_document_matches,
        num_version_matches=num_version_matches,
        percent_document_matches=percent_document_matches,
        percent_version_matches=percent_version_matches,
        now=now,
        icon_date_url=icon_date_url
    )

    template = jinja_env \
        .get_template('search_results_documents.html')

    documents_html = template.render(
        num_documents=num_document_matches,
        documents=documents
    )

    template = jinja_env \
        .get_template('search_results.html')

    search_results_html = template.render(
        num_documents=num_document_matches,
        documents=documents
    )

    with fitz.open() as pdf:
        insert_html_as_pdf(pdf, cover_page_html)
        insert_html_as_pdf(pdf, documents_html)
        insert_html_as_pdf(
            pdf,
            search_results_html,
            page_margins=(25, 25, 25, 20)
        )

        for i in range(1, pdf.page_count):
            page = pdf.load_page(i)

            insert_text_into_pdf_page(
                page=page,
                text=str(i),
                horizontal_align_text='center',
                vertical_align_text='bottom',
                color=(0.5, 0.5, 0.5),
                vertical_offset=10,
                font_size=9
            )

            insert_text_into_pdf_page(
                page=page,
                text=now,
                horizontal_align_text='right',
                vertical_align_text='top',
                color=(0.5, 0.5, 0.5),
                vertical_offset=15,
                font_size=9
            )

            insert_text_into_pdf_page(
                page=page,
                text='COVID-19 Guidance Explorer: Search Results',
                horizontal_align_text='left',
                vertical_align_text='top',
                color=(0.5, 0.5, 0.5),
                vertical_offset=15,
                font_size=9
            )

        pdf.save(save_file)

    return save_file

def generate_search_results_report(
    search_string: str,
    *,
    search_mode: Literal[
        'phrase', 'simple', 'plain',
        'normal', 'string', 'regex'
    ] = 'normal',
    case_sensitive: Optional[bool]=False,
    file_type: Literal['csv', 'xlsx', 'pdf']='csv'
) -> Path:
    save_file = Path(config['paths']['temp_dir']) \
        .joinpath(f'{uuid4()}.{file_type}')

    if file_type == 'pdf':
        return generate_search_results_pdf_report(
            search_string=search_string,
            search_mode=search_mode,
            case_sensitive=case_sensitive
        )

    search_results = search(
        search_string=search_string,
        search_mode=search_mode,
        case_sensitive=case_sensitive,
    )

    cleaned_search_results = []

    for i, search_result in enumerate(search_results):
        search_result['effective_date'] = search_result['effective_date'] \
                .strftime('%Y-%m-%d')

        if search_result['termination_date'] is None:
            search_result['termination_date'] = 'N/A'
        else:
            search_result['termination_date'] = search_result['termination_date'] \
                .strftime('%Y-%m-%d')

        if search_result['headline'] == '':
            search_result['headline'] = 'No Headline'
        else:
            search_result['headline'] = search_result['headline'].replace('\n', '<br/>')

        search_result['headline'] = clean_headline(search_result['headline'])

        search_result['version_num'] = i + 1

        cleaned_search_results.append(search_result)

    cleaned_search_results = pd \
        .DataFrame(cleaned_search_results) \
        .loc[:, [
            'version_num', 'document_id', 'id', 'title', 'slug',
            'effective_date', 'termination_date', 'headline'
        ]] \
        .set_axis([
            'Version #', 'Document ID', 'ID', 'Title', 'Slug',
            'Effective Date', 'Termination Date', 'Headline'
        ], axis=1)

    if file_type == 'csv':
        cleaned_search_results.to_csv(save_file, index=False)
    elif file_type == 'xlsx':
        cleaned_search_results.to_excel(
            save_file,
            sheet_name='Search Results',
            index=False
        )
    else:
        raise ValueError("The file type must be either 'csv' or 'xlsx'.")

    return save_file

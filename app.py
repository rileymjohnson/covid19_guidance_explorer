from flask_admin.contrib.rediscli import RedisCli
from flask_admin.contrib.peewee import ModelView
from flask_admin import Admin
from flask import Flask

from dash import Dash, CeleryManager, page_registry
from celery import Celery
from redis import Redis
from furl import furl

from covid19_guidance_explorer.config import config
from covid19_guidance_explorer.layout import layout
from covid19_guidance_explorer.database import (
    Tag,
    DocumentTagThroughTable,
    Jurisdiction,
    DocumentJurisdictionThroughTable,
    DocumentType,
    DocumentDocumentTypeThroughTable,
    FileType,
    Language,
    DocumentIssuer,
    DocumentVersionTagThroughTable,
    DocumentVersionJurisdictionThroughTable,
    DocumentVersionDocumentTypeThroughTable,
    Document,
    DocumentVersion,
)


server = Flask(__name__)

server.config["SECRET_KEY"] = config["general"]["secret_key"]

if not config["general"]["debug"]:
    server.config["FLASK_ADMIN_SWATCH"] = config["general"]["bootswatch_theme"]

    admin = Admin(
        server,
        name=config["general"]["title"],
        template_mode="bootstrap4"
    )

    admin.add_view(ModelView(Tag, category="Document Attributes"))
    admin.add_view(ModelView(Jurisdiction, category="Document Attributes"))
    admin.add_view(ModelView(DocumentType, category="Document Attributes"))
    admin.add_view(ModelView(FileType, category="Document Attributes"))
    admin.add_view(ModelView(Language, category="Document Attributes"))
    admin.add_view(
        ModelView(
            DocumentTagThroughTable,
            category="Through Tables"
        )
    )
    admin.add_view(
        ModelView(
            DocumentJurisdictionThroughTable,
            category="Through Tables"
        )
    )
    admin.add_view(
        ModelView(
            DocumentDocumentTypeThroughTable,
            category="Through Tables"
        )
    )
    admin.add_view(
        ModelView(
            DocumentVersionTagThroughTable,
            category="Through Tables"
        )
    )
    admin.add_view(
        ModelView(
            DocumentVersionJurisdictionThroughTable,
            category="Through Tables"
        )
    )
    admin.add_view(
        ModelView(
            DocumentVersionDocumentTypeThroughTable,
            category="Through Tables"
        )
    )
    admin.add_view(ModelView(Document, category="Documents"))
    admin.add_view(ModelView(DocumentVersion, category="Documents"))
    admin.add_view(ModelView(DocumentIssuer, category="Documents"))

    redis = Redis(**config["redis"])

    admin.add_view(RedisCli(redis))

redis_base_url = furl(scheme="redis", **config["redis"])

celery_app = Celery(
    __name__,
    broker=redis_base_url.copy().set(path="0").url,
    backend=redis_base_url.copy().set(path="1").url,
)

background_callback_manager = CeleryManager(celery_app)

app = Dash(
    server=server,
    assets_folder=config["paths"]["assets_folder"],
    pages_folder=config["paths"]["pages_folder"],
    include_assets_files=False,
    update_title=None,
    use_pages=True,
    background_callback_manager=background_callback_manager,
    title=config["general"]["title"],
    external_stylesheets=[
        (
            "https://cdn.jsdelivr.net/npm/bootstrap-icons"
            "@1.10.3/font/bootstrap-icons.css"
        ),
        (
            "https://cdn.jsdelivr.net/npm/bootswatch@5.2.3/dist/"
            f'{config["general"]["bootswatch_theme"]}/bootstrap.min.css'
        ),
        "/assets/styles.css",
    ],
    external_scripts=["/assets/utils.js"],
)

app.layout = layout(page_registry)
app._favicon = "favicon.ico"

if __name__ == "__main__":
    if config["general"]["debug"]:
        app.run(
            host=config["general"]["host"],
            port=config["general"]["port"],
            dev_tools_serve_dev_bundles=True,
            dev_tools_prune_errors=False,
            dev_tools_props_check=True,
            dev_tools_hot_reload=True,
            dev_tools_ui=True,
            debug=True,
        )
    else:
        app.run(
            host=config["general"]["host"],
            port=config["general"]["port"],
            dev_tools_ui=False,
            debug=False,
        )

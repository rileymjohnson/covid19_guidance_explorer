import dash

from covid19app.config import config


def register_page(*, title, **kwargs):
    dash.register_page(
        title=f'{config["general"]["title"]} - {title}',
        name=title,
        **kwargs
    )

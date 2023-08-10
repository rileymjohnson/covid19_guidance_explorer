import dash_bootstrap_components as dbc
from dash import html, dcc

from covid19_guidance_explorer.pages import register_page


def layout() -> html.Div:
    return dcc.Link(
        dbc.Alert(
            [
                html.I(className='bi bi-x-octagon-fill me-2'),
                html.Span(
                    '404: Page not found. Click to return to the home page.'
                )
            ],
            color='danger',
            className='d-flex align-items-center',
        ),
        href='/',
        style={'textDecoration': 'none'}
    )


register_page(
    module=__name__,
    path=None,
    title='404',
    order=-1
)

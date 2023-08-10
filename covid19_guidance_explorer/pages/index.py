import dash_bootstrap_components as dbc
from dash import html, dcc

from covid19_guidance_explorer.pages import register_page


def layout() -> html.Div:
    return html.Div(
        dbc.Container(
            [
                html.H1(
                    'Welcome to the COVID-19 Guidance Explorer',
                    className='display-5'
                ),
                html.P(
                    ('Use this tool to view, annotate, and '
                        'search COVID-19 guidance documents'),
                    className='lead',
                ),
                html.Hr(className='my-2'),
                html.P(
                    dcc.Link(
                        dbc.Button(
                            'Explore the Documents',
                            color='primary'
                        ),
                        href='/documents'
                    ),
                    className='lead mt-3'
                ),
            ],
            fluid=True,
            className='py-3',
        ),
        className='p-3 bg-light rounded-3',
    )


register_page(
    module=__name__,
    path='/',
    title='Home',
    order=0,
    icon='house-door-fill'
)

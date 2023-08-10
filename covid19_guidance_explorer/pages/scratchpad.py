import dash_bootstrap_components as dbc
from dash import html, dcc

from datetime import datetime

from covid19_guidance_explorer.pages import register_page


def layout() -> html.Div:
    return html.Div(
        dbc.Container(
            [
                html.H1('Scratchpad', className='display-5'),
                html.Div(
                    [
                        dcc.RangeSlider(0, 20, 1, value=[5, 15])
                    ]
                ),
                html.Div(
                    [
                        dcc.Slider(0, 20, 5, value=10)
                    ]
                ),
                html.Div(
                    [
                        dcc.DatePickerSingle(
                            min_date_allowed=datetime(2020, 1, 1),
                            max_date_allowed=datetime(2022, 12, 31),
                            initial_visible_month=datetime(2020, 1, 1),
                            display_format='YYYY-MM-DD',
                            date=datetime(2020, 1, 16)
                        )
                    ]
                ),
                html.Div(
                    [
                        dcc.DatePickerRange(
                            min_date_allowed=datetime(2020, 1, 1),
                            max_date_allowed=datetime(2022, 12, 31),
                            initial_visible_month=datetime(2020, 1, 1),
                            display_format='YYYY-MM-DD',
                            start_date=datetime(2020, 1, 13),
                            end_date=datetime(2020, 5, 28)
                        )
                    ]
                )
            ],
            fluid=True,
            className='py-3',
        ),
        className='p-3 bg-light rounded-3',
    )


register_page(
    module=__name__,
    path='/scratchpad',
    title='Scratchpad',
    order=7,
    icon='stickies-fill'
)

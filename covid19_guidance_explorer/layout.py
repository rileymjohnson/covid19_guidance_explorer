from dash import Input, Output, State, html, dcc, page_container, clientside_callback, ALL
import dash_bootstrap_components as dbc

from covid19_guidance_explorer.config import config


clientside_callback(
    """
    () => {
        return (
            dash_clientside.callback_context.triggered[0].prop_id
             === 'layout-navbar-button.n_clicks'
        )
    }
    """,
    Output('layout-side-navbar', 'is_open'),
    Input('layout-navbar-button', 'n_clicks'),
    Input({'type': 'navbar-link', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)

clientside_callback(
    """
    (_, __, searchText) => {
        if (searchText !== '') {
            httpGetArgs = Object
                .entries({
                    search_string: searchText,
                    search_mode: 'simple',
                    case_sensitive: false,
                    k: 0,
                    n: 5
                })
                .map(([a, v]) => `${a}=${v}`)
                .join('&')

            return `/search-results?${httpGetArgs}`
        } else {
            return dash_clientside.no_update
        }
    }
    """,
    Output('layout-location', 'href'),
    Input('layout-navbar-search-input', 'n_submit'),
    Input('layout-navbar-search-button', 'n_clicks'),
    State('layout-navbar-search-input', 'value'),
    prevent_initial_call=True
)

def layout(page_registry):
    navbar_links = []

    for page in sorted(page_registry.values(), key=lambda p: p['order']):
        if page['order'] != -1:
            navbar_links.append(
                dbc.ListGroupItem(
                    html.Div(
                        [
                            html.I(className=f'bi bi-{page.get("icon", "search")}'),
                            html.Span(page['name'])
                        ]
                    ),
                    href=page['path'],
                    id={'type': 'navbar-link', 'index': page['path']},
                    class_name='list-group-item-with-icon'
                )
            )

    return html.Div([
        dcc.Location(id='layout-location'),
        dbc.Offcanvas(
            dbc.ListGroup(
                navbar_links,
                flush=True
            ),
            id='layout-side-navbar',
            title='Menu',
            is_open=False,
        ),
        dbc.Navbar(
            dbc.Container(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Button(
                                        html.I(className='bi bi-list h3 lh-1'),
                                        id='layout-navbar-button',
                                        class_name='p-1',
                                        n_clicks=0
                                    ),
                                    dcc.Link(
                                        dbc.NavbarBrand(
                                            config['general']['title'],
                                            className='ms-2 align-middle'
                                        ),
                                        href='/'
                                    )
                                ],
                                width=6,
                                class_name='p-0'
                            ),
                            dbc.Col(
                                dbc.InputGroup(
                                    [
                                        dbc.InputGroupText(
                                            html.I(className='bi bi-search')
                                        ),
                                        dbc.Input(
                                            value='',
                                            placeholder='Search...',
                                            id='layout-navbar-search-input'
                                        ),
                                        dbc.Button(
                                            'Search',
                                            id='layout-navbar-search-button'
                                        )
                                    ],
                                    class_name='p-0'
                                ),
                                width={'size': 4, 'offset': 2},
                                align='center',
                                class_name='p-0'
                            )
                        ],
                        class_name='w-100 m-0'
                    )
                ],
                class_name='m-0',
                fluid=True
            ),
            color='dark',
            dark=True,
            class_name='py-2'
        ),
        dbc.Container(
            page_container,
            class_name='mt-3',
            fluid=True
        )
    ])

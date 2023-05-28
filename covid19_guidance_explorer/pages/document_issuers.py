from dash import html, dcc, Output, Input, State, callback, clientside_callback
import dash_bootstrap_components as dbc

from covid19_guidance_explorer.database import DocumentIssuer
from covid19_guidance_explorer.pages import register_page


@callback(
    Output('document-issuers-table-pagination', 'max_value'),
    Output('document-issuers-table-container', 'children'),
    Input('document-issuers-table-search-input', 'n_submit'),
    Input('document-issuers-table-search-button', 'n_clicks'),
    Input('document-issuers-table-pagination', 'active_page'),
    Input('document-issuers-table-rows-per-page', 'value'),
    State('document-issuers-table-search-input', 'value')
)
def handled_table(_, __, page, rows_per_page, search_text):
    search_string = None if search_text == '' else search_text
    n = int(rows_per_page)

    document_issuers = DocumentIssuer.get_values(
        k=page - 1,
        n=n,
        search_string=search_string
    )

    num_pages = DocumentIssuer.get_num_pages(
        n=n,
        search_string=search_string
    )

    table_body = [
        html.Tr([
            html.Td(
                html.Img(
                    src=issuer.icon_url,
                    title=issuer.short_name,
                    alt=f'{issuer.short_name} Icon',
                    className='rounded',
                    width='60',
                    height='60'
                ),
                className='d-flex justify-content-center align-items-center'
            ),
            html.Td(issuer.short_name),
            html.Td(issuer.long_name),
            html.Td(f'{issuer.num_documents:,}'),
            html.Td(f'{issuer.num_document_versions:,}')
        ])
    for issuer in document_issuers]

    table = dbc.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th('Icon', className='text-nowrap'),
                        html.Th('Issuer Short Name', className='text-nowrap'),
                        html.Th('Issuer Long Name', className='text-nowrap'),
                        html.Th('# Documents', className='text-nowrap'),
                        html.Th('# Document Versions', className='text-nowrap')
                    ]
                )
            ),
            html.Tbody(table_body)
        ],
        bordered=True
    )

    return num_pages, table

clientside_callback(
    """
    () => (
        dash_clientside.callback_context.triggered[0]?.prop_id !==
            'document-issuers-table-pagination.active_page' ? 1 : dash_clientside.no_update
    )
    """,
    Output('document-issuers-table-pagination', 'active_page'),
    Input('document-issuers-table-search-input', 'n_submit'),
    Input('document-issuers-table-search-button', 'n_clicks'),
    Input('document-issuers-table-pagination', 'active_page'),
    Input('document-issuers-table-rows-per-page', 'value')
)

def layout() -> html.Div:
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.H1('Document Issuers', className='h3'),
                        width=6
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
                                    id='document-issuers-table-search-input'
                                ),
                                dbc.Button(
                                    'Search',
                                    id='document-issuers-table-search-button'
                                )
                            ],
                            class_name='p-0'
                        ),
                        width={'size': 3, 'offset': 3}
                    )
                ],
                class_name='mb-1'
            ),
            dcc.Loading(
                id='document-issuers-table-container',
                className='table-loader'
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label('Rows per page', class_name='small mb-0'),
                            dbc.Select(
                                options=[{'label': i, 'value': i} for i in range(1, 11)],
                                id='document-issuers-table-rows-per-page',
                                value=5
                            )
                        ],
                        width=2,
                        style={
                            'position': 'relative',
                            'bottom': '10px'
                        }
                    ),
                    dbc.Col(
                        dbc.Pagination(
                            active_page=1,
                            max_value=1,
                            fully_expanded=False,
                            previous_next=True,
                            first_last=True,
                            style={'float': 'right'},
                            id='document-issuers-table-pagination'
                        ),
                        width=10
                    )
                ]
            )
        ]
    )

register_page(
    module=__name__,
    path='/document-issuers',
    title='Document Issuers',
    order=1,
    icon='building-fill'
)

from dash import html, dcc, Output, Input, State, callback, clientside_callback
import dash_bootstrap_components as dbc

from covid19app.pages import register_page
from covid19app.database import Document


@callback(
    Output('documents-table-pagination', 'max_value'),
    Output('documents-table-container', 'children'),
    Input('documents-table-search-input', 'n_submit'),
    Input('documents-table-search-button', 'n_clicks'),
    Input('documents-table-pagination', 'active_page'),
    Input('documents-table-rows-per-page', 'value'),
    State('documents-table-search-input', 'value')
)
def handled_table(_, __, page, rows_per_page, search_text):
    search_string = None if search_text == '' else search_text
    n = int(rows_per_page)

    documents = Document.get_values(
        k=page,
        n=n,
        search_string=search_string
    )

    num_pages = Document.get_num_pages(
        n=n,
        search_string=search_string
    )

    table_body = [
        html.Tr([
            html.Td(document.effective_date.strftime('%Y-%m-%d')),
            html.Td(
                '' if document.termination_date is None \
                    else document.termination_date.strftime('%Y-%m-%d')
            ),
            html.Td(document.slug),
            html.Td(document.title),
            html.Td(f'{document.num_versions:,}'),
            html.Td(
                [
                    dbc.Badge(
                        t['text'],
                        pill=True,
                        color=t['color'],
                        className='me-1'
                    )
                for t in getattr(document, 'tags', [])]
            ),
            html.Td(
                dcc.Link(
                    [
                        dbc.Button(
                            html.I(className='bi bi-info-circle'),
                            id={
                                'type': 'documents-info-button',
                                'index': i
                            },
                            color='primary'
                        ),
                        dbc.Tooltip(
                            'View document info',
                            target={
                                'type': 'documents-info-button',
                                'index': i
                            },
                            class_name='tooltip-no-arrow',
                            placement='left',
                        )
                    ],
                    href=f'/document/{document.id}'
                )
            )
        ])
    for i, document in enumerate(documents)]

    table = dbc.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th('Effective Date', className='text-nowrap'),
                        html.Th('Termination Date', className='text-nowrap'),
                        html.Th('Document Slug', className='text-nowrap'),
                        html.Th('Title', className='text-nowrap'),
                        html.Th('# Versions', className='text-nowrap'),
                        html.Th('Tags', className='text-nowrap'),
                        html.Th('')
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
            'documents-table-pagination.active_page' ? 1 : dash_clientside.no_update
    )
    """,
    Output('documents-table-pagination', 'active_page'),
    Input('documents-table-search-input', 'n_submit'),
    Input('documents-table-search-button', 'n_clicks'),
    Input('documents-table-pagination', 'active_page'),
    Input('documents-table-rows-per-page', 'value')
)

def layout() -> html.Div:
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.H1('Documents', className='h3'),
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
                                    id='documents-table-search-input'
                                ),
                                dbc.Button(
                                    'Search',
                                    id='documents-table-search-button'
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
                id='documents-table-container',
                className='table-loader'
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label('Rows per page', class_name='small mb-0'),
                            dbc.Select(
                                options=[{'label': i, 'value': i} for i in range(1, 11)],
                                id='documents-table-rows-per-page',
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
                            id='documents-table-pagination'
                        ),
                        width=10
                    )
                ]
            )
        ]
    )

register_page(
    module=__name__,
    path='/documents',
    title='Documents',
    order=2,
    icon='file-earmark-text-fill'
)

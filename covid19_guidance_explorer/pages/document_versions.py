from dash import html, dcc, Output, Input, State, callback, clientside_callback
import dash_bootstrap_components as dbc

from covid19_guidance_explorer.database import DocumentVersion
from covid19_guidance_explorer.pages import register_page


@callback(
    Output('document-versions-table-pagination', 'max_value'),
    Output('document-versions-table-container', 'children'),
    Input('document-versions-table-search-input', 'n_submit'),
    Input('document-versions-table-search-button', 'n_clicks'),
    Input('document-versions-table-pagination', 'active_page'),
    Input('document-versions-table-rows-per-page', 'value'),
    State('document-versions-table-search-input', 'value')
)
def handled_table(_, __, page, rows_per_page, search_text):
    search_string = None if search_text == '' else search_text
    n = int(rows_per_page)

    document_versions = DocumentVersion.get_values(
        k=page,
        n=n,
        search_string=search_string,
        quick_search=True
    )

    num_pages = DocumentVersion.get_num_pages(
        n=n,
        search_string=search_string,
        quick_search=True
    )
    
    table_body = [
        html.Tr([
            html.Td(
                html.Img(
                    src=document_version.icon_url,
                    title=document_version.title,
                    alt=f'{document_version.title} Icon',
                    className='rounded border border-2 shadow-sm',
                    width='100',
                    height='100'
                )
            ),
            html.Td(document_version.effective_date.strftime('%Y-%m-%d')),
            html.Td(
                '' if document_version.termination_date is None \
                    else document_version.termination_date.strftime('%Y-%m-%d')
            ),
            html.Td(document_version.slug),
            html.Td(document_version.title),
            html.Td(f'{document_version.version_num:,}'),
            html.Td(
                [
                    dbc.Badge(
                        t['text'],
                        pill=True,
                        color=t['color'],
                        className='me-1'
                    )
                for t in getattr(document_version, 'tags', []) or []]
            ),
            html.Td(
                dcc.Link(
                    [
                        dbc.Button(
                            html.I(className='bi bi-info-circle'),
                            id={
                                'type': 'document-versions-info-button',
                                'index': document_version.id
                            },
                            color='primary'
                        ),
                        dbc.Tooltip(
                            'View document info',
                            target={
                                'type': 'document-versions-info-button',
                                'index': document_version.id
                            },
                            class_name='tooltip-no-arrow',
                            placement='left',
                        )
                    ],
                    href=f'/document-version/{document_version.id}'
                )
            )
        ])
    for document_version in document_versions]

    table = dbc.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th('Icon', className='text-nowrap'),
                        html.Th('Effective Date', className='text-nowrap'),
                        html.Th('Termination Date', className='text-nowrap'),
                        html.Th('Document Slug', className='text-nowrap'),
                        html.Th('Title', className='text-nowrap'),
                        html.Th('Version #', className='text-nowrap'),
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
            'document-versions-table-pagination.active_page' ? 1 : dash_clientside.no_update
    )
    """,
    Output('document-versions-table-pagination', 'active_page'),
    Input('document-versions-table-search-input', 'n_submit'),
    Input('document-versions-table-search-button', 'n_clicks'),
    Input('document-versions-table-pagination', 'active_page'),
    Input('document-versions-table-rows-per-page', 'value')
)

def layout() -> html.Div:
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.H1('Document Versions', className='h3'),
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
                                    id='document-versions-table-search-input'
                                ),
                                dbc.Button(
                                    'Search',
                                    id='document-versions-table-search-button'
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
                id='document-versions-table-container',
                className='table-loader'
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label('Rows per page', class_name='small mb-0'),
                            dbc.Select(
                                options=[{'label': i, 'value': i} for i in range(1, 11)],
                                id='document-versions-table-rows-per-page',
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
                            id='document-versions-table-pagination'
                        ),
                        width=10
                    )
                ]
            )
        ]
    )

register_page(
    module=__name__,
    path='/document-versions',
    title='Document Versions',
    order=3,
    icon='git'
)

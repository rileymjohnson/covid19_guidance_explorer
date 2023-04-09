from dash import html, dcc, Output, Input, State, MATCH, callback, clientside_callback
from dash_dangerously_set_inner_html import DangerouslySetInnerHTML
import dash_bootstrap_components as dbc
from typing import Dict
import pandas as pd
import math

from covid19app.reports import generate_search_results_report
from covid19app.search import search, search_num_results
from covid19app.pages import register_page


search_modes = ('phrase', 'simple', 'plain', 'normal', 'string', 'regex')

def parse_http_get_args(http_get_args: Dict[str, str]) -> Dict[str, str | int | bool]:
    if 'search_string' not in http_get_args:
        raise ValueError('A search_string argument is required.')

    search_string = http_get_args['search_string']

    search_mode = http_get_args.get('search_mode')

    if search_mode not in search_modes:
        if search_mode is None:
            search_mode = 'simple'
        else:
            raise ValueError('The search_mode passed is not a valid search mode.')

    case_sensitive = http_get_args \
        .get('case_sensitive', '') \
        .title()

    if case_sensitive == 'False':
        case_sensitive = False
    elif case_sensitive == 'True':
        case_sensitive = True
    else:
        raise ValueError('The case_sensitive passed is not a boolean string.')

    try:
        k = int(http_get_args.get('k', '0'))
    except ValueError:
        raise ValueError('The k value passed is not a valid int.')

    try:
        n = int(http_get_args.get('n', '5'))
    except ValueError:
        raise ValueError('The n value passed is not a valid int.')

    return {
        'search_string': search_string,
        'search_mode': search_mode,
        'case_sensitive': case_sensitive,
        'k': k,
        'n': n
    }

clientside_callback(
    """
    () => (
        dash_clientside.callback_context.triggered[0].prop_id !==
          'search-results-search-query-modal-close-button.n_clicks'
    )
    """,
    Output('search-results-search-query-modal', 'is_open'),
    Input('search-results-open-search-query-modal', 'n_clicks'),
    Input('search-results-search-query-modal-close-button', 'n_clicks'),
    prevent_initial_call=True
)

clientside_callback(
    """
    (_, isOpen) => {
        return [
            !isOpen,
            isOpen ? 'bi bi-chevron-down h4' : 'bi bi-chevron-up h4'
        ]
    }
    """,
    Output({'type': 'search-results-item-collapse', 'index': MATCH}, 'is_open'),
    Output({'type': 'search-results-item-button-icon', 'index': MATCH}, 'className'),
    Input({'type': 'search-results-item-button', 'index': MATCH}, 'n_clicks'),
    State({'type': 'search-results-item-collapse', 'index': MATCH}, 'is_open'),
    prevent_initial_call=True
)

clientside_callback(
    """
    (rows_per_page, page_number, args) => {
        const url = new URL(window.location)
        url.searchParams.set('k', page_number - 1)
        url.searchParams.set('n', rows_per_page)
        window.history.pushState({}, '', url.toString())
        return {
            ...args,
            k: Number(page_number - 1),
            n: Number(rows_per_page)
        }
    }
    """,
    Output('search-results-args', 'data'),
    Input('search-results-rows-per-page', 'value'),
    Input('search-results-pagination', 'active_page'),
    State('search-results-args', 'data'),
    prevent_initial_call=True
)

@callback(
    Output('search-results-download-csv', 'data'),
    Input('search-results-export-as-csv', 'n_clicks'),
    State('search-results-args', 'data'),
    prevent_initial_call=True
)
def search_results_handle_export_as_csv(_, search_args):
    file = generate_search_results_report(
        search_string=search_args['search_string'],
        search_mode=search_args['search_mode'],
        case_sensitive=search_args['case_sensitive'],
        file_type='csv'
    )

    return dcc.send_file(file)

@callback(
    Output('search-results-download-xlsx', 'data'),
    Input('search-results-export-as-xlsx', 'n_clicks'),
    State('search-results-args', 'data'),
    prevent_initial_call=True
)
def search_results_handle_export_as_xlsx(_, search_args):
    file = generate_search_results_report(
        search_string=search_args['search_string'],
        search_mode=search_args['search_mode'],
        case_sensitive=search_args['case_sensitive'],
        file_type='xlsx'
    )

    return dcc.send_file(file)

@callback(
    Output('search-results-download-pdf', 'data'),
    Input('search-results-export-as-pdf', 'n_clicks'),
    State('search-results-args', 'data'),
    prevent_initial_call=True
)
def search_results_handle_export_as_pdf(_, search_args):
    file = generate_search_results_report(
        search_string=search_args['search_string'],
        search_mode=search_args['search_mode'],
        case_sensitive=search_args['case_sensitive'],
        file_type='pdf'
    )

    return dcc.send_file(file)

@callback(
    Output('search-results-list', 'children'),
    Output('search-results-num-documents', 'children'),
    Output('search-results-num-document-versions', 'children'),
    Output('search-results-pagination', 'max_value'),
    Input('search-results-args', 'data')
)
def search_results_handle_args_change(http_get_args):
    list_rows = []

    results = pd.DataFrame(search(**http_get_args))

    if results.shape[0] == 0:
        return [], 0, 0, 1
    else:
        num_results = search_num_results(
            search_string=http_get_args['search_string'],
            search_mode=http_get_args['search_mode'],
            case_sensitive=http_get_args['case_sensitive']
        )

        num_results_documents = num_results.get(
            'num_documents',
            0
        )

        num_results_document_versions = num_results.get(
            'num_document_versions',
            0
        )

        num_pagination_pages = math.ceil(
            num_results_documents / http_get_args.get('n', 1)
        )

    results = results.groupby('document_id')

    for i, (document_id, group) in enumerate(results):
        group_url = f'/document/{document_id}'
        title = group.title.mode().iloc[0]
        slug = group.slug.mode().iloc[0]

        effective_date = group.effective_date.min()

        if effective_date is None or pd.isna(effective_date):
            effective_date = 'N/A'
        else:
            effective_date = effective_date.strftime('%Y-%m-%d')

        termination_date = group.termination_date.max()

        if termination_date is None or pd.isna(termination_date):
            termination_date = 'N/A'
        else:
            termination_date = termination_date.strftime('%Y-%m-%d')

        group_versions = group \
            .sort_values('effective_date') \
            .iterrows()

        group_rows = []

        for j, group_version in group_versions:
            version_url = f'/document-version/{group_version.id}'

            version_effective_date = group_version.effective_date

            if version_effective_date is None or pd.isna(version_effective_date):
                version_effective_date = 'N/A'
            else:
                version_effective_date = version_effective_date.strftime('%Y-%m-%d')

            version_termination_date = group_version.termination_date

            if version_termination_date is None or pd.isna(version_termination_date):
                version_termination_date = 'N/A'
            else:
                version_termination_date = version_termination_date.strftime('%Y-%m-%d')

            if group_version.headline != '':
                headline = group_version.headline
            else:
                headline = 'No Headline'

            group_row = dbc.Table(
                [
                    html.Thead(
                        html.Tr(
                            [
                                html.Th('Version #', className='text-nowrap'),
                                html.Th('Effective Date', className='text-nowrap'),
                                html.Th('Termination Date', className='text-nowrap'),
                                html.Th('')
                            ]
                        )
                    ),
                    html.Tbody(
                        [
                            html.Tr(
                                [
                                    html.Td(str(j + 1)),
                                    html.Td(version_effective_date),
                                    html.Td(version_termination_date),
                                    html.Td(
                                        dcc.Link(
                                            dbc.Button(
                                                html.I(className='bi bi-info-circle')
                                            ),
                                            href=version_url,
                                            style={'float': 'right'}
                                        )
                                    )
                                ]
                            ),
                            html.Tr(
                                html.Td(
                                    [
                                        DangerouslySetInnerHTML(headline)    
                                    ],
                                    colSpan=4
                                )
                            )
                        ]
                    )
                ]
            )

            group_rows.append(group_row)

        row_num = http_get_args.get('n', 5) * \
            http_get_args.get('k', 0) + i + 1

        list_row = dbc.ListGroupItem(
            [
                html.Div(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.H5(
                                        dbc.Badge(
                                            str(row_num),
                                            class_name='circle-number'
                                        ),
                                        className='m-0'
                                    ),
                                    width='auto',
                                    class_name='d-flex align-items-center'
                                ),
                                dbc.Col(
                                    [
                                        dcc.Link(
                                            html.H5(
                                                title,
                                                className='mb-0'
                                            ) if title != '' else dbc.Alert(
                                                'No Title',
                                                class_name='fs-6 py-1 px-2 d-table mb-1 mt-1',
                                                color='danger'
                                            ),
                                            className='styleless-link',
                                            href=group_url
                                        ),
                                        dcc.Link(
                                            html.Small(
                                                slug,
                                                className='text-muted'
                                            ),
                                            className='styleless-link',
                                            href=group_url
                                        )
                                    ]
                                )
                            ],
                            class_name='g-3'
                        ),
                        html.Div(
                            [
                                html.Small(
                                    f'{effective_date} — {termination_date}',
                                    className='text-muted'
                                ),
                                dbc.Button(
                                    html.I(
                                        className='bi bi-chevron-down h4',
                                        id={
                                            'type': 'search-results-item-button-icon',
                                            'index': i
                                        }
                                    ),
                                    color='light',
                                    class_name='p-0 button-no-outline',
                                    id={
                                        'type': 'search-results-item-button',
                                        'index': i
                                    },
                                )
                            ],
                            className='d-flex flex-column align-items-end'
                        )
                    ],
                    className='d-flex w-100 justify-content-between',
                ),
                dbc.Collapse(
                    dbc.Card(
                        dbc.CardBody(group_rows)
                    ),
                    id={
                        'type': 'search-results-item-collapse',
                        'index': i
                    },
                    class_name='mt-1',
                    is_open=False
                )
            ]
        )

        list_rows.append(list_row)

    return (
        list_rows,
        num_results_documents,
        num_results_document_versions,
        num_pagination_pages
    )

def layout(**http_get_args) -> html.Div:
    try:
        http_get_args = parse_http_get_args(http_get_args)
    except ValueError:
        http_get_args = {}

    search_text = http_get_args.get('search_string', '')
    search_mode = http_get_args.get('search_mode', 'Unknown')

    if http_get_args.get('case_sensitive', False):
        case_sensitive = 'Yes'
    else:
        case_sensitive = 'No'

    return html.Div(
        [
            dcc.Download(id='search-results-download-csv'),
            dcc.Download(id='search-results-download-xlsx'),
            dcc.Download(id='search-results-download-pdf'),
            dcc.Store(id='search-results-args', data=http_get_args),
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle('Search Query'),
                        close_button=True
                    ),
                    dbc.ModalBody(
                        [
                            dbc.Row(
                                dbc.Col(
                                    [
                                        dbc.Label('Search Text'),
                                        dbc.Input(
                                            value=search_text,
                                            type='text',
                                            disabled=True,
                                            style={'pointerEvents': 'none'}
                                        )
                                    ]
                                )
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label('Search Mode'),
                                            dbc.Select(
                                                options=[
                                                    'phrase', 'simple', 'plain',
                                                    'normal', 'string', 'regex'
                                                ],
                                                value=search_mode,
                                                disabled=True,
                                                style={
                                                    'backgroundColor': '#d4d4d4'
                                                }
                                            )
                                        ]
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label('Case Sensitive'),
                                            dbc.Input(
                                                value=case_sensitive,
                                                type='text',
                                                disabled=True,
                                                style={'pointerEvents': 'none'}
                                            )
                                        ]
                                    )
                                ],
                                class_name='mt-2'
                            )
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                'Close',
                                color='warning',
                                id='search-results-search-query-modal-close-button'
                            )
                        ]
                    ),
                ],
                id='search-results-search-query-modal',
                centered=True,
                is_open=False,
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Alert(
                            dbc.Spinner(
                                html.H1(
                                    [
                                        html.I(className='bi bi-search me-2'),
                                        html.Span(
                                            '',
                                            className='fw-bold',
                                            id='search-results-num-documents'
                                        ),
                                        html.Span(' documents and '),
                                        html.Span(
                                            '',
                                            className='fw-bold',
                                            id='search-results-num-document-versions'
                                        ),
                                        html.Span(' versions found...')
                                    ],
                                    className='h6 fst-italic mb-0'
                                ),
                                size='sm'
                            ),
                            color='success',
                            class_name='mb-0',
                            style={
                                'width': 'fit-content',
                                'padding': '10px'
                            }
                        )
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                dbc.DropdownMenu(
                                    [
                                        dbc.DropdownMenuItem(
                                            'Search Query',
                                            id='search-results-open-search-query-modal'
                                        ),
                                        dbc.DropdownMenuItem(
                                            'Analytics'
                                        ),
                                        dbc.DropdownMenuItem(divider=True),
                                        dbc.DropdownMenuItem(
                                            'Export as PDF',
                                            id='search-results-export-as-pdf'
                                        ),
                                        dbc.DropdownMenuItem(
                                            'Export as CSV',
                                            id='search-results-export-as-csv'
                                        ),
                                        dbc.DropdownMenuItem(
                                            'Export as XLSX',
                                            id='search-results-export-as-xlsx'
                                        )
                                    ],
                                    label='Options',
                                    align_end=True,
                                    style={'textAlign': 'right'}
                                )
                            ]
                        ),
                        width='auto'
                    )
                ],
                class_name='mb-2'
            ),
            dbc.Spinner(
                dbc.ListGroup(
                    children=[],
                    flush=True,
                    id='search-results-list',
                ),
                color='success',
                size='xl'
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label('Rows per page', class_name='small mb-0 mt-1'),
                            dbc.Select(
                                options=[{'label': i, 'value': i} for i in range(1, 11)],
                                value=http_get_args.get('n', 5),
                                id='search-results-rows-per-page'
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
                            active_page=http_get_args.get('k', 0) + 1,
                            max_value=1,
                            fully_expanded=False,
                            previous_next=True,
                            first_last=True,
                            style={'float': 'right'},
                            id='search-results-pagination'
                        ),
                        width=10
                    )
                ]
            )
        ]
    )

register_page(
    module=__name__,
    path='/search-results',
    title='Search Results',
    order=-1
)

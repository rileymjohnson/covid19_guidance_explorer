from dash import html, dcc, Output, Input, State, callback, clientside_callback, ALL
import dash_bootstrap_components as dbc

from covid19_guidance_explorer.pages import register_page
from covid19_guidance_explorer.database import (
    DocumentVersionDocumentTypeThroughTable,
    DocumentDocumentTypeThroughTable,
    DocumentType
)


clientside_callback(
    """
    (buttonClicks) => {
        const prop_id = dash_clientside.callback_context.triggered[0]?.prop_id
        if ([
            'document-types-delete-are-you-sure-modal-cancel-button.n_clicks',
            'document-types-delete-are-you-sure-modal-delete-button.n_clicks'
        ].includes(prop_id)) {
            return [null, false]
        } else if (!buttonClicks.every(i => i === undefined)) {
            const { id } = parsePatternMatchingId(prop_id)
            return [id.index, true]
        }

        return [dash_clientside.no_update, false]
    }
    """,
    Output('document-types-delete-store', 'data'),
    Output('document-types-delete-are-you-sure-modal', 'is_open'),
    Input({'type': 'document-types-delete-button', 'index': ALL}, 'n_clicks'),
    Input('document-types-delete-are-you-sure-modal-delete-button', 'n_clicks'),
    Input('document-types-delete-are-you-sure-modal-cancel-button', 'n_clicks'),
    prevent_initial_call=True
)


@callback(
    Output('document-types-delete-toast', 'is_open'),
    Input('document-types-delete-are-you-sure-modal-delete-button', 'n_clicks'),
    State('document-types-delete-store', 'data'),
    prevent_initial_call=True
)
def document_types_delete_handler(_, document_type_id):
    DocumentDocumentTypeThroughTable \
        .delete() \
        .where(DocumentDocumentTypeThroughTable.document_type_id == document_type_id) \
        .execute()

    DocumentVersionDocumentTypeThroughTable \
        .delete() \
        .where(DocumentVersionDocumentTypeThroughTable.document_type_id == document_type_id) \
        .execute()

    DocumentType \
        .delete() \
        .where(DocumentType.id == document_type_id) \
        .execute()

    return True


clientside_callback(
    """
    (a, b, c, label, value) => {
        if (
            dash_clientside.callback_context.triggered[0]?.prop_id ===
                'document-types-add-document-type-modal-save-button.n_clicks'
        ) {
            return [false, { label, value }]
        }

        return [
            dash_clientside.callback_context.triggered[0]?.prop_id ===
                'document-types-add-document-type-button.n_clicks',
            dash_clientside.no_update
        ]
    }
    """,
    Output('document-types-add-document-type-modal', 'is_open'),
    Output('document-types-new-store', 'data'),
    Input('document-types-add-document-type-button', 'n_clicks'),
    Input('document-types-add-document-type-modal-save-button', 'n_clicks'),
    Input('document-types-add-document-type-modal-cancel-button', 'n_clicks'),
    State('document-types-add-document-type-modal-label-input', 'value'),
    State('document-types-add-document-type-modal-value-input', 'value'),
    prevent_initial_call=True
)


@callback(
    Output('document-types-new-toast', 'is_open'),
    Input('document-types-new-store', 'data'),
    prevent_initial_call=True
)
def document_types_new_handler(data):
    DocumentType.create(**data)
    return True


clientside_callback(
    """
    () => ['', '']
    """,
    Output('document-types-add-document-type-modal-label-input', 'value'),
    Output('document-types-add-document-type-modal-value-input', 'value'),
    Input('document-types-add-document-type-modal', 'is_open')
)


@callback(
    Output('document-types-table-pagination', 'max_value'),
    Output('document-types-table-container', 'children'),
    Input('document-types-table-search-input', 'n_submit'),
    Input('document-types-table-search-button', 'n_clicks'),
    Input('document-types-table-pagination', 'active_page'),
    Input('document-types-table-rows-per-page', 'value'),
    Input('document-types-new-store', 'data'),
    Input('document-types-delete-are-you-sure-modal-delete-button', 'n_clicks'),
    State('document-types-table-search-input', 'value')
)
def handled_table(_, __, page, rows_per_page, ___, ____, search_text):
    search_string = None if search_text == '' else search_text
    n = int(rows_per_page)

    document_types = DocumentType.get_values(
        k=page,
        n=n,
        search_string=search_string
    )

    num_pages = DocumentType.get_num_pages(
        n=n,
        search_string=search_string
    )

    table_body = [
        html.Tr([
            html.Td(document_type.id),
            html.Td(document_type.label),
            html.Td(document_type.value),
            html.Td(
                [
                    dbc.Button(
                        html.I(className='bi bi-trash'),
                        color='danger',
                        id={
                            'type': 'document-types-delete-button',
                            'index': document_type.id
                        }
                    ),
                    dbc.Tooltip(
                        'Delete document type',
                        target={
                            'type': 'document-types-delete-button',
                            'index': document_type.id
                        },
                        class_name='tooltip-no-arrow',
                        placement='left',
                    )
                ],
                className='text-center',
                style={'width': '70px'}
            )
        ])
        for document_type in document_types
    ]

    table = dbc.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th('Database ID', className='text-nowrap'),
                        html.Th('Label', className='text-nowrap'),
                        html.Th('Value', className='text-nowrap'),
                        html.Th('', style={'width': '70px'})
                    ]
                )
            ),
            html.Tbody(table_body)
        ],
        bordered=True,
        style={'tableLayout': 'fixed'}
    )

    return num_pages, table


clientside_callback(
    """
    () => (
        dash_clientside.callback_context.triggered[0]?.prop_id !==
            'document-types-table-pagination.active_page' ? 1 : dash_clientside.no_update
    )
    """,
    Output('document-types-table-pagination', 'active_page'),
    Input('document-types-table-search-input', 'n_submit'),
    Input('document-types-table-search-button', 'n_clicks'),
    Input('document-types-table-pagination', 'active_page'),
    Input('document-types-table-rows-per-page', 'value')
)


def layout() -> html.Div:
    return html.Div(
        [
            dbc.Toast(
                [
                    html.P('The document type has been added.', className='mb-0')
                ],
                header='Success',
                icon='success',
                duration=4000,
                is_open=False,
                id='document-types-new-toast',
                style={
                    'position': 'fixed',
                    'top': 66,
                    'right': 10,
                    'width': 350
                }
            ),
            dbc.Toast(
                [
                    html.P('The document type has been deleted.', className='mb-0')
                ],
                header='Success',
                icon='success',
                duration=4000,
                is_open=False,
                id='document-types-delete-toast',
                style={
                    'position': 'fixed',
                    'top': 66,
                    'right': 10,
                    'width': 350
                }
            ),
            dcc.Store(id='document-types-delete-store'),
            dcc.Store(id='document-types-new-store'),
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle(
                            'Are you sure?'
                        ),
                        close_button=True
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                'Delete',
                                className='ms-auto',
                                color='danger',
                                id='document-types-delete-are-you-sure-modal-delete-button'
                            ),
                            dbc.Button(
                                'Cancel',
                                color='warning',
                                id='document-types-delete-are-you-sure-modal-cancel-button'
                            )
                        ]
                    ),
                ],
                id='document-types-delete-are-you-sure-modal',
                centered=True,
                is_open=False,
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle('Add Document Type'),
                        close_button=True
                    ),
                    dbc.ModalBody(
                        [
                            dbc.Row(
                                dbc.Col(
                                    [
                                        dbc.Label('Label'),
                                        dbc.Input(
                                            type='text',
                                            placeholder='Enter label here...',
                                            id='document-types-add-document-type-modal-label-input'
                                        )
                                    ]
                                )
                            ),
                            dbc.Row(
                                dbc.Col(
                                    [
                                        dbc.Label('Value'),
                                        dbc.Input(
                                            type='text',
                                            placeholder='Enter value here...',
                                            id='document-types-add-document-type-modal-value-input'
                                        )
                                    ]
                                ),
                                class_name='mt-2'
                            )
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                'Save',
                                className='ms-auto',
                                color='success',
                                id='document-types-add-document-type-modal-save-button'
                            ),
                            dbc.Button(
                                'Cancel',
                                color='warning',
                                id='document-types-add-document-type-modal-cancel-button'
                            )
                        ]
                    ),
                ],
                id='document-types-add-document-type-modal',
                centered=True,
                is_open=False,
            ),
            dbc.Row(
                [
                    dbc.Col(
                        html.H1('Document Types', className='h3'),
                        width=5
                    ),
                    dbc.Col(
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Button(
                                        html.Div(
                                            [
                                                html.I(className='bi bi-plus-lg h5'),
                                                html.Span('Add Document Type')
                                            ]
                                        ),
                                        color='info',
                                        class_name='button-with-icon',
                                        id='document-types-add-document-type-button',
                                        style={'padding': '5.09px 12px'}
                                    ),
                                    style={'textAlign': 'right'},
                                    width='auto'
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
                                                id='document-types-table-search-input'
                                            ),
                                            dbc.Button(
                                                'Search',
                                                id='document-types-table-search-button'
                                            )
                                        ],
                                        class_name='p-0'
                                    )
                                )
                            ],
                            class_name='g-3'
                        ),
                        width={'size': 6, 'offset': 1}
                    )
                ],
                class_name='mb-1'
            ),
            dcc.Loading(
                id='document-types-table-container',
                className='table-loader'
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label('Rows per page', class_name='small mb-0'),
                            dbc.Select(
                                options=[{'label': i, 'value': i} for i in range(1, 11)],
                                id='document-types-table-rows-per-page',
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
                            id='document-types-table-pagination'
                        ),
                        width=10
                    )
                ]
            )
        ]
    )


register_page(
    module=__name__,
    path='/document-types',
    title='Document Types',
    order=6,
    icon='file-x-fill'
)

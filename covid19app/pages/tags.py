from dash import html, dcc, Output, Input, State, callback, clientside_callback, ALL
import dash_bootstrap_components as dbc

from covid19app.pages import register_page
from covid19app.database import (
    DocumentVersionTagThroughTable,
    DocumentTagThroughTable,
    Tag
)


clientside_callback(
    """
    (buttonClicks) => {
        const prop_id = dash_clientside.callback_context.triggered[0]?.prop_id
        if ([
            'tags-delete-are-you-sure-modal-cancel-button.n_clicks',
            'tags-delete-are-you-sure-modal-delete-button.n_clicks'
        ].includes(prop_id)) {
            return [null, false]
        } else if (!buttonClicks.every(i => i === undefined)) {
            const { id } = parsePatternMatchingId(prop_id)
            return [id.index, true]
        }
        
        return [dash_clientside.no_update, false]
    }
    """,
    Output('tags-delete-store', 'data'),
    Output('tags-delete-are-you-sure-modal', 'is_open'),
    Input({'type': 'tags-delete-button', 'index': ALL}, 'n_clicks'),
    Input('tags-delete-are-you-sure-modal-delete-button', 'n_clicks'),
    Input('tags-delete-are-you-sure-modal-cancel-button', 'n_clicks'),
    prevent_initial_call=True
)

@callback(
    Output('tags-delete-toast', 'is_open'),
    Input('tags-delete-are-you-sure-modal-delete-button', 'n_clicks'),
    State('tags-delete-store', 'data'),
    prevent_initial_call=True
)
def tags_delete_handler(_, tag_id):
    DocumentTagThroughTable \
        .delete() \
        .where(DocumentTagThroughTable.tag_id == tag_id) \
        .execute()

    DocumentVersionTagThroughTable \
        .delete() \
        .where(DocumentVersionTagThroughTable.tag_id == tag_id) \
        .execute()

    Tag \
        .delete() \
        .where(Tag.id == tag_id) \
        .execute()

    return True

clientside_callback(
    """
    (a, b, c, text, color) => {
        if (
            dash_clientside.callback_context.triggered[0]?.prop_id ===
                'tags-add-tag-modal-save-button.n_clicks'
        ) {
            return [false, { text, color }]
        }

        return [
            dash_clientside.callback_context.triggered[0]?.prop_id ===
                'tags-add-tag-button.n_clicks',
            dash_clientside.no_update
        ]
    }
    """,
    Output('tags-add-tag-modal', 'is_open'),
    Output('tags-new-store', 'data'),
    Input('tags-add-tag-button', 'n_clicks'),
    Input('tags-add-tag-modal-save-button', 'n_clicks'),
    Input('tags-add-tag-modal-cancel-button', 'n_clicks'),
    State('tags-add-tag-modal-text-input', 'value'),
    State('tags-add-tag-modal-color-input', 'value'),
    prevent_initial_call=True
)

@callback(
    Output('tags-new-toast', 'is_open'),
    Input('tags-new-store', 'data'),
    prevent_initial_call=True
)
def tags_new_handler(data):
    Tag.create(**data)
    return True

clientside_callback(
    """
    () => ['', '']
    """,
    Output('tags-add-tag-modal-text-input', 'value'),
    Output('tags-add-tag-modal-color-input', 'value'),
    Input('tags-add-tag-modal', 'is_open')
)

@callback(
    Output('tags-table-pagination', 'max_value'),
    Output('tags-table-container', 'children'),
    Input('tags-table-search-input', 'n_submit'),
    Input('tags-table-search-button', 'n_clicks'),
    Input('tags-table-pagination', 'active_page'),
    Input('tags-table-rows-per-page', 'value'),
    Input('tags-new-store', 'data'),
    Input('tags-delete-are-you-sure-modal-delete-button', 'n_clicks'),
    State('tags-table-search-input', 'value')
)
def handled_table(_, __, page, rows_per_page, ___, ____, search_text):
    search_string = None if search_text == '' else search_text
    n = int(rows_per_page)

    tags = Tag.get_values(
        k=page,
        n=n,
        search_string=search_string
    )

    num_pages = Tag.get_num_pages(
        n=n,
        search_string=search_string
    )

    table_body = [
        html.Tr([
            html.Td(tag.id),
            html.Td(tag.text),
            html.Td(
                html.Span(
                    tag.color,
                    style={
                        'background': tag.color,
                        'padding': '6px',
                        'borderRadius': '5px'
                    }
                ),
                className='text-center'
            ),
            html.Td(
                [
                    dbc.Button(
                        html.I(className='bi bi-trash'),
                        color='danger',
                        id={
                            'type': 'tags-delete-button',
                            'index': tag.id
                        }
                    ),
                    dbc.Tooltip(
                    'Delete tag',
                        target={
                            'type': 'tags-delete-button',
                            'index': tag.id
                        },
                        class_name='tooltip-no-arrow',
                        placement='left',
                    )
                ],
                className='text-center',
                style={'width': '70px'}
            )
        ])
    for tag in tags]

    table = dbc.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th('Database ID', className='text-nowrap'),
                        html.Th('Tag', className='text-nowrap'),
                        html.Th('Color', className='text-nowrap'),
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
            'tags-table-pagination.active_page' ? 1 : dash_clientside.no_update
    )
    """,
    Output('tags-table-pagination', 'active_page'),
    Input('tags-table-search-input', 'n_submit'),
    Input('tags-table-search-button', 'n_clicks'),
    Input('tags-table-pagination', 'active_page'),
    Input('tags-table-rows-per-page', 'value')
)

def layout() -> html.Div:
    return html.Div(
        [
            dbc.Toast(
                [
                    html.P('The tag has been added.', className='mb-0')
                ],
                header='Success',
                icon='success',
                duration=4000,
                is_open=False,
                id='tags-new-toast',
                style={
                    'position': 'fixed',
                    'top': 66,
                    'right': 10,
                    'width': 350
                }
            ),
            dbc.Toast(
                [
                    html.P('The tag has been deleted.', className='mb-0')
                ],
                header='Success',
                icon='success',
                duration=4000,
                is_open=False,
                id='tags-delete-toast',
                style={
                    'position': 'fixed',
                    'top': 66,
                    'right': 10,
                    'width': 350
                }
            ),
            dcc.Store(id='tags-delete-store'),
            dcc.Store(id='tags-new-store'),
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
                                id='tags-delete-are-you-sure-modal-delete-button'
                            ),
                            dbc.Button(
                                'Cancel',
                                color='warning',
                                id='tags-delete-are-you-sure-modal-cancel-button'
                            )
                        ]
                    ),
                ],
                id='tags-delete-are-you-sure-modal',
                centered=True,
                is_open=False,
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle('Add Tag'),
                        close_button=True
                    ),
                    dbc.ModalBody(
                        [
                            dbc.Row(
                                dbc.Col(
                                    [
                                        dbc.Label('Text'),
                                        dbc.Input(
                                            type='text',
                                            placeholder='Enter text here...',
                                            id='tags-add-tag-modal-text-input'
                                        )
                                    ]
                                )
                            ),
                            dbc.Row(
                                dbc.Col(
                                    [
                                        dbc.Label('Color'),
                                        dbc.Input(
                                            type='color',
                                            value='#000000',
                                            style={
                                                'width': '75px',
                                                'height': '50px',
                                                'cursor': 'pointer',
                                                'margin': 'auto'
                                            },
                                            id='tags-add-tag-modal-color-input'
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
                                id='tags-add-tag-modal-save-button'
                            ),
                            dbc.Button(
                                'Cancel',
                                color='warning',
                                id='tags-add-tag-modal-cancel-button'
                            )
                        ]
                    ),
                ],
                id='tags-add-tag-modal',
                centered=True,
                is_open=False,
            ),
            dbc.Row(
                [
                    dbc.Col(
                        html.H1('Tags', className='h3'),
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
                                                html.Span('Add Tag')
                                            ]
                                        ),
                                        color='info',
                                        class_name='button-with-icon',
                                        id='tags-add-tag-button',
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
                                                id='tags-table-search-input'
                                            ),
                                            dbc.Button(
                                                'Search',
                                                id='tags-table-search-button'
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
                id='tags-table-container',
                className='table-loader'
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label('Rows per page', class_name='small mb-0'),
                            dbc.Select(
                                options=[{'label': i, 'value': i} for i in range(1, 11)],
                                id='tags-table-rows-per-page',
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
                            id='tags-table-pagination'
                        ),
                        width=10
                    )
                ]
            )
        ]
    )

register_page(
    module=__name__,
    path='/tags',
    title='Tags',
    order=4,
    icon='tag-fill'
)

from dash import html, dcc, Output, Input, State, callback, clientside_callback
import dash_bootstrap_components as dbc
from dash_quill import Quill
import json

from covid19app.pages import register_page
from covid19app.database import (
    Document,
    Language,
    FileType,
    Tag,
    Jurisdiction,
    DocumentType,
    DocumentDocumentTypeThroughTable,
    DocumentJurisdictionThroughTable,
    DocumentTagThroughTable
)


review_checklist_items = [
    {
        'label': 'Importance',
        'value': 'importance'
    },
    {
        'label': 'Has Relevant Information',
        'value': 'has_relevant_information'
    },
    {
        'label': 'Is Foreign Language',
        'value': 'is_foreign_language'
    },
    {
        'label': 'Is Malformed',
        'value': 'is_malformed'
    },
    {
        'label': 'Is Empty',
        'value': 'is_empty'
    },
    {
        'label': 'Title',
        'value': 'title'
    },
    {
        'label': 'Document Slug',
        'value': 'slug'
    },
    {
        'label': 'Source',
        'value': 'source'
    },
    {
        'label': 'Source Notes',
        'value': 'source_notes'
    },
    {
        'label': 'Language',
        'value': 'language'
    },
    {
        'label': 'File Type',
        'value': 'file_type'
    },
    {
        'label': 'Tags',
        'value': 'tags'
    },
    {
        'label': 'Jurisdictions',
        'value': 'jurisdictions'
    },
    {
        'label': 'Document Types',
        'value': 'document_types'
    },
    {
        'label': 'Notes',
        'value': 'notes'
    },
    {
        'label': 'Variables',
        'value': 'variables'
    },
]

modal_add_models = {
    'language': Language,
    'jurisdiction': Jurisdiction,
    'document-type': DocumentType
}

def document_add_handler_wrapper(field):
    def handler(data):
        model = modal_add_models[field]
        model.create(**data)

        return True, model.get_select_values()

    return handler

clientside_callback(
    f"""
    ({{ length }}) => {{
        return [
            length / {len(review_checklist_items)} * 100,
            `${{length}} / {len(review_checklist_items)}`
        ]
    }}
    """,
    Output('document-review-checklist-progress-bar', 'value'),
    Output('document-review-checklist-progress-bar', 'label'),
    Input('document-review-checklist', 'value'),
    prevent_initial_call=True
)

clientside_callback(
    """
    () => dash_clientside.callback_context.triggered[0].prop_id ===
          'document-review-checklist-button.n_clicks'
    """,
    Output('document-review-checklist-modal', 'is_open'),
    Input('document-review-checklist-modal-close-button', 'n_clicks'),
    Input('document-review-checklist-button', 'n_clicks'),
    prevent_initial_call=True
)

for field in ['language', 'jurisdiction', 'document-type']:
    clientside_callback(
        f"""
        (a, b, c, label, value) => {{
            const prop_id = dash_clientside.callback_context.triggered[0].prop_id
            if (prop_id === 'document-add-{field}-button.n_clicks') {{
                return [true, dash_clientside.no_update]
            }} else if (prop_id === 'document-add-{field}-modal-save-button.n_clicks') {{
                return [false, {{ label, value }}]
            }}

            return [false, dash_clientside.no_update]
        }}
        """,
        Output(f'document-add-{field}-modal', 'is_open'),
        Output(f'document-add-{field}-store', 'data'),
        Input(f'document-add-{field}-button', 'n_clicks'),
        Input(f'document-add-{field}-modal-save-button', 'n_clicks'),
        Input(f'document-add-{field}-modal-cancel-button', 'n_clicks'),
        State(f'document-add-{field}-modal-label-input', 'value'),
        State(f'document-add-{field}-modal-value-input', 'value'),
        prevent_initial_call=True
    )

    clientside_callback(
        """
        () => ['', '']
        """,
        Output(f'document-add-{field}-modal-label-input', 'value'),
        Output(f'document-add-{field}-modal-value-input', 'value'),
        Input(f'document-add-{field}-modal', 'is_open'),
        prevent_initial_call=True
    )

    callback(
        Output(f'document-add-{field}-toast', 'is_open'),
        Output(f'document-{field}', 'options'),
        Input(f'document-add-{field}-store', 'data'),
        prevent_initial_call=True
    )(document_add_handler_wrapper(field))

clientside_callback(
    """
    (a, b, c, text, color) => {
        const prop_id = dash_clientside.callback_context.triggered[0].prop_id
        if (prop_id === 'document-add-tag-button.n_clicks') {
            return [true, dash_clientside.no_update]
        } else if (prop_id === 'document-add-tag-modal-save-button.n_clicks') {
            return [false, { text, color }]
        }

        return [false, dash_clientside.no_update]
    }
    """,
    Output('document-add-tag-modal', 'is_open'),
    Output('document-add-tag-store', 'data'),
    Input('document-add-tag-button', 'n_clicks'),
    Input('document-add-tag-modal-save-button', 'n_clicks'),
    Input('document-add-tag-modal-cancel-button', 'n_clicks'),
    State('document-add-tag-modal-text-input', 'value'),
    State('document-add-tag-modal-color-input', 'value'),
    prevent_initial_call=True
)

clientside_callback(
    """
    () => ['', '#000000']
    """,
    Output('document-add-tag-modal-text-input', 'value'),
    Output('document-add-tag-modal-color-input', 'value'),
    Input('document-add-tag-modal', 'is_open'),
    prevent_initial_call=True
)

@callback(
    Output('document-add-tag-toast', 'is_open'),
    Output('document-tags', 'options'),
    Input('document-add-tag-store', 'data'),
    prevent_initial_call=True
)
def document_add_tag_handler(data):
    Tag.create(**data)
    return True, Tag.get_select_values()

clientside_callback(
    """
    (a, b, c, label, suffix, mimetype) => {
        const prop_id = dash_clientside.callback_context.triggered[0].prop_id
        if (prop_id === 'document-add-file-type-button.n_clicks') {
            return [true, dash_clientside.no_update]
        } else if (prop_id === 'document-add-file-type-modal-save-button.n_clicks') {
            return [false, { label, suffix, mimetype }]
        }

        return [false, dash_clientside.no_update]
    }
    """,
    Output('document-add-file-type-modal', 'is_open'),
    Output('document-add-file-type-store', 'data'),
    Input('document-add-file-type-button', 'n_clicks'),
    Input('document-add-file-type-modal-save-button', 'n_clicks'),
    Input('document-add-file-type-modal-cancel-button', 'n_clicks'),
    State('document-add-file-type-modal-label-input', 'value'),
    State('document-add-file-type-modal-suffix-input', 'value'),
    State('document-add-file-type-modal-mimetype-input', 'value'),
    prevent_initial_call=True
)

clientside_callback(
    """
    () => ['', '', '']
    """,
    Output('document-add-file-type-modal-label-input', 'value'),
    Output('document-add-file-type-modal-suffix-input', 'value'),
    Output('document-add-file-type-modal-mimetype-input', 'value'),
    Input('document-add-file-type-modal', 'is_open'),
    prevent_initial_call=True
)

@callback(
    Output('document-add-file-type-toast', 'is_open'),
    Output('document-file-type', 'options'),
    Input('document-add-file-type-store', 'data'),
    prevent_initial_call=True
)
def document_add_file_type_handler(data):
    FileType.create(**data)
    return True, FileType.get_select_values()

clientside_callback(
    """
    () => (
        dash_clientside.callback_context.triggered[0]?.prop_id ===
            'document-delete-document-button.n_clicks'
    )
    """,
    Output('document-delete-document-modal', 'is_open'),
    Input('document-delete-document-button', 'n_clicks'),
    Input('document-delete-document-modal-cancel-button', 'n_clicks'),
    Input('document-delete-document-modal-delete-button', 'n_clicks'),
    prevent_initial_call=True
)

@callback(
    Output('document-delete-toast', 'is_open'),
    Input('document-delete-document-modal-delete-button', 'n_clicks'),
    State('document-data-store', 'data'),
    prevent_initial_call=True
)
def document_delete_document_handler(_, data):
    print('deleting document', data['document_id'])
    return True

clientside_callback(
    """
    (...args) => {
        const [
            review_switches, importance, check_boxes, title, slug, source,
            source_notes, language, file_type, tags, jurisdictions,
            document_types, notes, variables, review_checklist_values, data
        ] = args

        const reviewed = review_switches.includes('reviewed')
        const flagged_for_review = review_switches.includes('flagged_for_review')

        const has_relevant_information = check_boxes.includes('has_relevant_information')
        const is_foreign_language = check_boxes.includes('is_foreign_language')
        const is_malformed = check_boxes.includes('is_malformed')
        const is_empty = check_boxes.includes('is_empty')

        const review_checklist = review_checklist_values.reduce(
            (t, x) => ({ [x]: true, ... t}), {}
        )

        return [
            {
                ...data,
                reviewed, flagged_for_review, importance, has_relevant_information,
                is_foreign_language, is_malformed, is_empty, title, slug, source,
                source_notes, language, file_type, tags, jurisdictions,
                document_types, notes, variables, review_checklist
            },
            false
        ]
    }
    """,
    Output('document-data-store', 'data'),
    Output('document-save-button', 'disabled'),
    Input('document-review-switches', 'value'),
    Input('document-importance', 'value'),
    Input('document-switches', 'value'),
    Input('document-title', 'value'),
    Input('document-slug', 'value'),
    Input('document-source', 'value'),
    Input('document-source-notes', 'value'),
    Input('document-language', 'value'),
    Input('document-file-type', 'value'),
    Input('document-tags', 'value'),
    Input('document-jurisdiction', 'value'),
    Input('document-document-type', 'value'),
    Input('document-notes', 'value'),
    Input('document-variables', 'value'),
    Input('document-review-checklist', 'value'),
    State('document-data-store', 'data'),
    prevent_initial_call=True
)

@callback(
    Output('document-save-toast', 'is_open'),
    Input('document-save-button', 'n_clicks'),
    State('document-data-store', 'data'),
    prevent_initial_call=True
)
def document_save_handler(_, data):
    document_id = int(data.pop('document_id'))
    tags = data.pop('tags', [])
    jurisdictions = data.pop('jurisdictions', [])
    document_types = data.pop('document_types', [])
    data['variables'] = json.loads(data['variables'])

    Document \
        .update(**data) \
        .where(Document.id == document_id) \
        .execute()

    for field_name, values, through_table in [
        ('tag', tags, DocumentTagThroughTable),
        ('jurisdiction', jurisdictions, DocumentJurisdictionThroughTable),
        ('document_type', document_types, DocumentDocumentTypeThroughTable)
    ]:
        through_table \
            .delete() \
            .where(through_table.document == document_id) \
            .execute()

        through_table \
            .insert_many([{
                'document': document_id,
                field_name: i
            } for i in values]) \
            .execute()
    return True

def layout(document_id=None) -> html.Div:
    if document_id is None:
        document = None
    else:
        document = Document.get_one(
            int(document_id)
        )

    importance = getattr(document, 'importance', None)
    title = getattr(document, 'title', '')
    slug = getattr(document, 'slug', '')

    effective_date = getattr(document, 'effective_date', None)
    termination_date = getattr(document, 'termination_date', None)

    effective_time = getattr(document, 'effective_date', None)

    if effective_time is not None:
        effective_time = effective_time.strftime('%H:%M:%S')

    termination_time = getattr(document, 'termination_date', None)

    if termination_time is not None:
        termination_time = termination_time.strftime('%H:%M:%S')

    num_versions = getattr(document, 'num_versions', None)

    database_id = getattr(document, 'id', '')

    source = getattr(document, 'source', '')
    source_notes = getattr(document, 'source_notes', '')

    document_issuer = getattr(document, 'issuer', None)

    if document_issuer is not None:
        document_issuer_short_name = getattr(document_issuer, 'short_name')
        document_issuer_long_name = getattr(document_issuer, 'long_name')
    else:
        document_issuer_short_name = ''
        document_issuer_long_name = ''

    notes = getattr(document, 'notes', '')
    variables = json.dumps(
        getattr(document, 'variables', '')
    )

    checkbox_fields = [
        'has_relevant_information', 'is_foreign_language',
        'is_malformed', 'is_empty'
    ]

    checkbox_values = [
        f for f in checkbox_fields if bool(getattr(document, f, None))
    ]

    review_fields = ['reviewed', 'flagged_for_review']
    review_switches = [
        f for f in review_fields if bool(getattr(document, f, None))
    ]

    file_type = getattr(document, 'file_type', None)
    file_type_value = getattr(file_type, 'id', None)

    language = getattr(document, 'language', None)
    language_value = getattr(language, 'id', None)

    tags = [t['id'] for t in getattr(document, 'tags', []) or []]
    jurisdictions = [
        t['id'] for t in getattr(document, 'jurisdictions', []) or []
    ]
    document_types = [
        t['id'] for t in getattr(document, 'types', []) or []
    ]

    review_checklist = [
        i for i, v in getattr(document, 'review_checklist', {}).items() if v
    ]
    review_checklist_completed = len(review_checklist)
    review_checklist_progress = review_checklist_completed / len(review_checklist_items) * 100
    review_checklist_progress_label = f'{review_checklist_completed} / {len(review_checklist_items)}'

    document_versions = [
        dbc.ListGroupItem(
            [
                html.Div(
                    [
                        html.H5(
                            dbc.Badge(
                                html.Span(f'{document_version["version_num"]}/{num_versions}'),
                                class_name='number-badge p-1'
                            ),
                            className='m-0 circle-number',
                        ),
                        html.Div(
                            [
                                html.H6(document_version['title']) if document_version['title'] \
                                    != '' else dbc.Badge('No title', color='danger', class_name='mb-2'),
                                html.P(
                                    '{}—{}'.format(
                                        document_version['effective_date'].strftime('%Y-%m-%d'),
                                        'N/A' if document_version['termination_date'] is None else \
                                            document_version['termination_date'].strftime('%Y-%m-%d')
                                    ),
                                    className='text-muted mb-0'
                                ),
                                html.Small(document_version['slug'], className='text-muted')
                            ]
                        )
                    ],
                    className='d-flex align-items-center',
                    style={'gap': '10px'}
                ),
                html.Div(
                    [
                        dcc.Link(
                            dbc.Button(
                                html.I(className='bi bi-eye-fill'),
                                color='info',
                                style={'height': 'fit-content'},
                                id={
                                    'index': 'document-document-versions-link',
                                    'type': document_version['id']
                                }
                            ),
                            href=f'/document-version/{document_version["id"]}'
                        ),
                        dbc.Tooltip(
                            'View document version',
                            target={
                                'index': 'document-document-versions-link',
                                'type': document_version['id']
                            },
                            class_name='tooltip-no-arrow',
                            placement='left',
                        )
                    ],
                )
            ],
            style={
                'display': 'flex',
                'justifyContent': 'space-between'
            },
            class_name='px-0'
        ) for document_version in getattr(document, 'versions', [])
    ]

    return html.Div(
        [
            dbc.Row(
                children=[
                    dbc.Col(
                        dbc.Container(
                            [
                                dbc.Toast(
                                    [
                                        html.P('Deleting documents is currently disabled.', className='mb-0')
                                    ],
                                    header='Error',
                                    icon='danger',
                                    duration=4000,
                                    is_open=False,
                                    id='document-delete-toast',
                                    style={
                                        'position': 'fixed',
                                        'top': 66,
                                        'right': 10,
                                        'width': 350
                                    }
                                ),
                                dbc.Toast(
                                    [
                                        html.P('The document has been saved.', className='mb-0')
                                    ],
                                    header='Success',
                                    icon='success',
                                    duration=4000,
                                    is_open=False,
                                    id='document-save-toast',
                                    style={
                                        'position': 'fixed',
                                        'top': 66,
                                        'right': 10,
                                        'width': 350
                                    }
                                ),
                                dbc.Modal(
                                    [
                                        dbc.ModalHeader(
                                            dbc.ModalTitle('Delete Document'),
                                            close_button=True
                                        ),
                                        dbc.ModalBody(
                                            [
                                                html.P(
                                                    'Are you sure that you want to delete this document? '
                                                    'It will not be possible to recover.'
                                                )
                                            ]
                                        ),
                                        dbc.ModalFooter(
                                            [
                                                dbc.Button(
                                                    'Delete',
                                                    className='ms-auto',
                                                    color='danger',
                                                    id='document-delete-document-modal-delete-button'
                                                ),
                                                dbc.Button(
                                                    'Cancel',
                                                    color='warning',
                                                    id='document-delete-document-modal-cancel-button'
                                                )
                                            ]
                                        ),
                                    ],
                                    id='document-delete-document-modal',
                                    centered=True,
                                    is_open=False,
                                ),
                                dcc.Store(
                                    id='document-data-store',
                                    data={
                                        'document_id': document_id
                                    }
                                ),
                                dcc.Store(
                                    id='document-add-language-store',
                                    data={}
                                ),
                                dcc.Store(
                                    id='document-add-jurisdiction-store',
                                    data={}
                                ),
                                dcc.Store(
                                    id='document-add-document-type-store',
                                    data={}
                                ),
                                dcc.Store(
                                    id='document-add-tag-store',
                                    data={}
                                ),
                                dcc.Store(
                                    id='document-add-file-type-store',
                                    data={}
                                ),
                                dbc.Modal(
                                    [
                                        dbc.ModalHeader(
                                            dbc.ModalTitle('Review Checklist'),
                                            close_button=True
                                        ),
                                        dbc.ModalBody(
                                            [
                                                dbc.Progress(
                                                    value=review_checklist_progress,
                                                    min=0,
                                                    max=100,
                                                    striped=True,
                                                    animated=True,
                                                    label=review_checklist_progress_label,
                                                    color='success',
                                                    class_name='border mb-3',
                                                    id='document-review-checklist-progress-bar'
                                                ),
                                                dbc.Checklist(
                                                    options=review_checklist_items,
                                                    value=review_checklist,
                                                    id='document-review-checklist'
                                                )
                                            ]
                                        ),
                                        dbc.ModalFooter(
                                            dbc.Button(
                                                'Close',
                                                className='ms-auto',
                                                id='document-review-checklist-modal-close-button'
                                            )
                                        ),
                                    ],
                                    id='document-review-checklist-modal',
                                    centered=True,
                                    is_open=False,
                                ),
                                dbc.Modal(
                                    [
                                        dbc.ModalHeader(
                                            dbc.ModalTitle('Add Language'),
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
                                                                id='document-add-language-modal-label-input'
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
                                                                id='document-add-language-modal-value-input'
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
                                                    id='document-add-language-modal-save-button'
                                                ),
                                                dbc.Button(
                                                    'Cancel',
                                                    color='warning',
                                                    id='document-add-language-modal-cancel-button'
                                                )
                                            ]
                                        ),
                                    ],
                                    id='document-add-language-modal',
                                    centered=True,
                                    is_open=False,
                                ),
                                dbc.Toast(
                                    [
                                        html.P('The language has been added.', className='mb-0')
                                    ],
                                    header='Success',
                                    icon='success',
                                    duration=4000,
                                    is_open=False,
                                    id='document-add-language-toast',
                                    style={
                                        'position': 'fixed',
                                        'top': 66,
                                        'right': 10,
                                        'width': 350
                                    }
                                ),
                                dbc.Modal(
                                    [
                                        dbc.ModalHeader(
                                            dbc.ModalTitle('Add Jurisdiction'),
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
                                                                id='document-add-jurisdiction-modal-label-input'
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
                                                                id='document-add-jurisdiction-modal-value-input'
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
                                                    id='document-add-jurisdiction-modal-save-button'
                                                ),
                                                dbc.Button(
                                                    'Cancel',
                                                    color='warning',
                                                    id='document-add-jurisdiction-modal-cancel-button'
                                                )
                                            ]
                                        ),
                                    ],
                                    id='document-add-jurisdiction-modal',
                                    centered=True,
                                    is_open=False,
                                ),
                                dbc.Toast(
                                    [
                                        html.P('The jurisdiction has been added.', className='mb-0')
                                    ],
                                    header='Success',
                                    icon='success',
                                    duration=4000,
                                    is_open=False,
                                    id='document-add-jurisdiction-toast',
                                    style={
                                        'position': 'fixed',
                                        'top': 66,
                                        'right': 10,
                                        'width': 350
                                    }
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
                                                                id='document-add-document-type-modal-label-input'
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
                                                                id='document-add-document-type-modal-value-input'
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
                                                    id='document-add-document-type-modal-save-button'
                                                ),
                                                dbc.Button(
                                                    'Cancel',
                                                    color='warning',
                                                    id='document-add-document-type-modal-cancel-button'
                                                )
                                            ]
                                        ),
                                    ],
                                    id='document-add-document-type-modal',
                                    centered=True,
                                    is_open=False,
                                ),
                                dbc.Toast(
                                    [
                                        html.P('The document type has been added.', className='mb-0')
                                    ],
                                    header='Success',
                                    icon='success',
                                    duration=4000,
                                    is_open=False,
                                    id='document-add-document-type-toast',
                                    style={
                                        'position': 'fixed',
                                        'top': 66,
                                        'right': 10,
                                        'width': 350
                                    }
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
                                                                id='document-add-tag-modal-text-input'
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
                                                                id='document-add-tag-modal-color-input'
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
                                                    id='document-add-tag-modal-save-button'
                                                ),
                                                dbc.Button(
                                                    'Cancel',
                                                    color='warning',
                                                    id='document-add-tag-modal-cancel-button'
                                                )
                                            ]
                                        ),
                                    ],
                                    id='document-add-tag-modal',
                                    centered=True,
                                    is_open=False,
                                ),
                                dbc.Toast(
                                    [
                                        html.P('The tag has been added.', className='mb-0')
                                    ],
                                    header='Success',
                                    icon='success',
                                    duration=4000,
                                    is_open=False,
                                    id='document-add-tag-toast',
                                    style={
                                        'position': 'fixed',
                                        'top': 66,
                                        'right': 10,
                                        'width': 350
                                    }
                                ),
                                dbc.Modal(
                                    [
                                        dbc.ModalHeader(
                                            dbc.ModalTitle('Add File Type'),
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
                                                                id='document-add-file-type-modal-label-input'
                                                            )
                                                        ]
                                                    )
                                                ),
                                                dbc.Row(
                                                    dbc.Col(
                                                        [
                                                            dbc.Label('Suffix'),
                                                            dbc.Input(
                                                                type='text',
                                                                placeholder='Enter suffix here...',
                                                                id='document-add-file-type-modal-suffix-input'
                                                            )
                                                        ]
                                                    ),
                                                    class_name='mt-2'
                                                ),
                                                dbc.Row(
                                                    dbc.Col(
                                                        [
                                                            dbc.Label('Mimetype'),
                                                            dbc.Input(
                                                                type='text',
                                                                placeholder='Enter mimetype here...',
                                                                id='document-add-file-type-modal-mimetype-input'
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
                                                    id='document-add-file-type-modal-save-button'
                                                ),
                                                dbc.Button(
                                                    'Cancel',
                                                    color='warning',
                                                    id='document-add-file-type-modal-cancel-button'
                                                )
                                            ]
                                        ),
                                    ],
                                    id='document-add-file-type-modal',
                                    centered=True,
                                    is_open=False,
                                ),
                                dbc.Toast(
                                    [
                                        html.P('The file type has been added.', className='mb-0')
                                    ],
                                    header='Success',
                                    icon='success',
                                    duration=4000,
                                    is_open=False,
                                    id='document-add-file-type-toast',
                                    style={
                                        'position': 'fixed',
                                        'top': 66,
                                        'right': 10,
                                        'width': 350
                                    }
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.ButtonGroup(
                                                [
                                                    dbc.Button(
                                                        html.Div(
                                                            [
                                                                html.I(className='bi bi-save h5'),
                                                                html.Span('Save')
                                                            ]
                                                        ),
                                                        disabled=True,
                                                        color='success',
                                                        className='button-with-icon',
                                                        id='document-save-button'
                                                    ),
                                                    dbc.Button(
                                                        html.Div(
                                                            [
                                                                html.I(className='bi bi-list-check h5'),
                                                                html.Span('Review Checklist')
                                                            ]
                                                        ),
                                                        color='info',
                                                        class_name='button-with-icon',
                                                        id='document-review-checklist-button'
                                                    ),
                                                    dbc.DropdownMenu(
                                                        [
                                                            dbc.DropdownMenuItem(
                                                                html.Span(
                                                                    [
                                                                        html.I(
                                                                            className='bi bi-trash dropdown-menu-icon'
                                                                        ),
                                                                        html.Span('Delete Document')
                                                                    ]
                                                                ),
                                                                id='document-delete-document-button'
                                                            )
                                                        ],
                                                        label='More',
                                                        color='warning',
                                                        group=True,
                                                    )
                                                ]
                                            ),
                                            class_name='text-center'
                                        )
                                    ],
                                    class_name='g-2 mt-0'
                                ),
                                html.Hr(className='mb-2 mt-3'),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Label('Importance'),
                                                dcc.Slider(
                                                    min=1,
                                                    max=10,
                                                    step=1,
                                                    id='document-importance',
                                                    value=importance
                                                )
                                            ]
                                        ),
                                        dbc.Col(
                                            dbc.Checklist(
                                                options=[
                                                    {
                                                        'label': 'Flagged for Review',
                                                        'value': 'flagged_for_review'
                                                    },
                                                    {
                                                        'label': 'Reviewed',
                                                        'value': 'reviewed'
                                                    },
                                                ],
                                                value=review_switches,
                                                inline=True,
                                                switch=True,
                                                input_checked_style={
                                                    'backgroundColor': '#fa7268',
                                                    'borderColor': '#ea6258'
                                                },
                                                class_name='form-check-lg',
                                                id='document-review-switches'
                                            ),
                                            width='auto'
                                        )
                                    ],
                                    class_name='g-3 mt-0'
                                ),
                                html.Hr(className='mb-2 mt-3'),
                                dbc.Row(
                                    dbc.Col(
                                        [
                                            dbc.Checklist(
                                                options=[
                                                    {
                                                        'label': 'Has Relevant Information',
                                                        'value': 'has_relevant_information'
                                                    },
                                                    {
                                                        'label': 'Is Foreign Language',
                                                        'value': 'is_foreign_language'
                                                    },
                                                    {
                                                        'label': 'Is Malformed',
                                                        'value': 'is_malformed'
                                                    },
                                                    {
                                                        'label': 'Is Empty',
                                                        'value': 'is_empty'
                                                    }
                                                ],
                                                value=checkbox_values,
                                                inline=True,
                                                id='document-switches'
                                            )
                                        ]
                                    ),
                                    class_name='g-2 mt-0'
                                ),
                                html.Hr(className='mb-2'),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Label('Title'),
                                                dbc.Input(
                                                    type='text',
                                                    value=title,
                                                    id='document-title'
                                                )
                                            ]
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Label('Document Slug'),
                                                dbc.Input(
                                                    type='text',
                                                    value=slug,
                                                    id='document-slug'
                                                )
                                            ]
                                        )
                                    ],
                                    class_name='g-2 mt-0'
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Label(
                                                    'Effective Date',
                                                    style={'width': '215%'}
                                                ),
                                                dcc.DatePickerSingle(
                                                    date=effective_date,
                                                    display_format='YYYY-MM-DD',
                                                    className='form-control form-control-date-picker',
                                                    disabled=True
                                                )
                                            ]
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Label('X', class_name='invisible'),
                                                dbc.Input(
                                                    type='time',
                                                    step=1,
                                                    class_name='form-control-time-picker',
                                                    value=effective_time,
                                                    disabled=True
                                                )
                                            ]
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Label(
                                                    'Termination Date',
                                                    style={'width': '215%'}
                                                ),
                                                dcc.DatePickerSingle(
                                                    date=termination_date,
                                                    display_format='YYYY-MM-DD',
                                                    className='form-control form-control-date-picker',
                                                    disabled=True
                                                )
                                            ]
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Label('X', class_name='invisible'),
                                                dbc.Input(
                                                    type='time',
                                                    step=1,
                                                    class_name='form-control-time-picker',
                                                    value=termination_time,
                                                    disabled=True
                                                )
                                            ]
                                        )
                                    ],
                                    class_name='g-2 mt-0'
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Label('Database ID'),
                                                dbc.Input(
                                                    type='number',
                                                    value=database_id,
                                                    disabled=True
                                                )
                                            ]
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Label('# Document Versions'),
                                                dbc.Input(
                                                    type='number',
                                                    value=num_versions,
                                                    disabled=True
                                                )
                                            ]
                                        )
                                    ],
                                    class_name='g-2 mt-0'
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Label('Document Issuer Short Name'),
                                                dbc.Input(
                                                    type='text',
                                                    value=document_issuer_short_name,
                                                    disabled=True
                                                )
                                            ]
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Label('Document Issuer Long Name'),
                                                dbc.Input(
                                                    type='text',
                                                    value=document_issuer_long_name,
                                                    disabled=True
                                                )
                                            ]
                                        )
                                    ],
                                    class_name='g-2 mt-0'
                                ),
                                dbc.Row(
                                    dbc.Col(
                                        [
                                            dbc.Label('Source'),
                                            dbc.InputGroup(
                                                [
                                                    dbc.Input(
                                                        type='text',
                                                        value=source,
                                                        id='document-source'
                                                    ),
                                                    dcc.Link(
                                                        dbc.Button(
                                                            html.I(className='bi bi-box-arrow-up-right')
                                                        ),
                                                        href=source,
                                                        target='_blank'
                                                    )
                                                ]
                                            )
                                        ]
                                    ),
                                    class_name='g-2 mt-0'
                                ),
                                dbc.Row(
                                    dbc.Col(
                                        [
                                            dbc.Label('Source Notes'),
                                            dbc.Input(
                                                placeholder='Put sources notes here...',
                                                type='text',
                                                value=source_notes,
                                                id='document-source-notes'
                                            )
                                        ]
                                    ),
                                    class_name='g-2 mt-0'
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Label('Language'),
                                                dbc.InputGroup(
                                                    [
                                                        dcc.Dropdown(
                                                            options=Language.get_select_values(),
                                                            value=language_value,
                                                            id='document-language'
                                                        ),
                                                        dbc.Button(
                                                            html.I(className='bi bi-plus h4'),
                                                            class_name='plus-button',
                                                            id='document-add-language-button'
                                                        )
                                                    ],
                                                    class_name='select-input-group'
                                                )
                                            ]
                                        )
                                    ],
                                    class_name='g-2 mt-0'
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Label('File Type'),
                                                dbc.InputGroup(
                                                    [
                                                        dcc.Dropdown(
                                                            options=FileType.get_select_values(),
                                                            value=file_type_value,
                                                            id='document-file-type'
                                                        ),
                                                        dbc.Button(
                                                            html.I(className='bi bi-plus h4'),
                                                            class_name='plus-button',
                                                            id='document-add-file-type-button'
                                                        )
                                                    ],
                                                    class_name='select-input-group'
                                                )
                                            ]
                                        )
                                    ],
                                    class_name='g-2 mt-0'
                                ),
                                dbc.Row(
                                    dbc.Col(
                                        [
                                            dbc.Label('Tags'),
                                            dbc.InputGroup(
                                                [
                                                    dcc.Dropdown(
                                                        options=Tag.get_select_values(),
                                                        value=tags,
                                                        multi=True,
                                                        id='document-tags'
                                                    ),
                                                    dbc.Button(
                                                        html.I(className='bi bi-plus h4'),
                                                        class_name='plus-button',
                                                        id='document-add-tag-button'
                                                    )
                                                ],
                                                class_name='select-input-group'
                                            )
                                        ]
                                    ),
                                    class_name='g-2 mt-0'
                                ),
                                dbc.Row(
                                    dbc.Col(
                                        [
                                            dbc.Label('Jurisdictions'),
                                            dbc.InputGroup(
                                                [
                                                    dcc.Dropdown(
                                                        options=Jurisdiction.get_select_values(),
                                                        value=jurisdictions,
                                                        multi=True,
                                                        id='document-jurisdiction'
                                                    ),
                                                    dbc.Button(
                                                        html.I(className='bi bi-plus h4'),
                                                        class_name='plus-button',
                                                        id='document-add-jurisdiction-button'
                                                    )
                                                ],
                                                class_name='select-input-group'
                                            )
                                        ]
                                    ),
                                    class_name='g-2 mt-0'
                                ),
                                dbc.Row(
                                    dbc.Col(
                                        [
                                            dbc.Label('Document Types'),
                                            dbc.InputGroup(
                                                [
                                                    dcc.Dropdown(
                                                        options=DocumentType.get_select_values(),
                                                        value=document_types,
                                                        multi=True,
                                                        id='document-document-type'
                                                    ),
                                                    dbc.Button(
                                                        html.I(className='bi bi-plus h4'),
                                                        class_name='plus-button',
                                                        id='document-add-document-type-button'
                                                    )
                                                ],
                                                class_name='select-input-group'
                                            )
                                        ]
                                    ),
                                    class_name='g-2 mt-0'
                                ),
                                dbc.Row(
                                    dbc.Col(
                                        [
                                            dbc.Label('Notes'),
                                            Quill(
                                                id='document-notes',
                                                value=notes,
                                                maxLength=10000,
                                                modules={
                                                    'toolbar': [
                                                        [
                                                            {'header': '1'},
                                                            {'header': '2'},
                                                            {'font': [] }
                                                        ],
                                                        [{'size': []}],
                                                        [
                                                            'bold', 'italic', 'underline',
                                                            'strike', 'blockquote'
                                                        ],
                                                        [
                                                            {'list': 'ordered'},
                                                            {'list': 'bullet'}
                                                        ]
                                                    ]
                                                }
                                            )
                                        ]
                                    ),
                                    class_name='g-2 mt-0'
                                ),
                                dbc.Row(
                                    dbc.Col(
                                        [
                                            dbc.Label('Variables'),
                                            dbc.Textarea(
                                                placeholder='X=5\nY=true\nZ="string"',
                                                id='document-variables',
                                                value=variables,
                                                rows=4
                                            )
                                        ]
                                    ),
                                    class_name='g-2 mt-0'
                                ),
                            ],
                            style={'overflowX': 'hidden', 'height': '100%'},
                            class_name='pb-3 fancy-scrollbar'
                        ),
                        width=6
                    ),
                    dbc.Col(
                        dbc.Container(
                            [
                                html.H1(
                                    'Versions',
                                    className='h5 mb-2 mt-2 text-center'
                                ),
                                html.Hr(className='mt-0'),
                                dbc.ListGroup(
                                    document_versions,
                                    flush=True
                                )
                            ]
                        ),
                        width=6,
                        class_name='pb-3 fancy-scrollbar'
                    ),
                ],
                class_name='two-column-fancy-scrollbar'
            )
        ]
    )

register_page(
    module=__name__,
    path='/document',
    path_template='/document/<document_id>',
    title='Document',
    order=-1
)

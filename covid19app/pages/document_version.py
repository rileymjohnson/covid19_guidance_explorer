from dash import html, dcc, Output, Input, State, callback, clientside_callback
from dash_split_pane import DashSplitPane
from dash_annotator import DashAnnotator
import dash_bootstrap_components as dbc
from dash_quill import Quill
import json

from covid19app.utils import base64_encode_file, load_file
from covid19app.pages import register_page
from covid19app.database import (
    DocumentVersion,
    Language, FileType,
    Tag,
    Jurisdiction,
    DocumentType,
    DocumentVersionDocumentTypeThroughTable,
    DocumentVersionJurisdictionThroughTable,
    DocumentVersionTagThroughTable
)

from selectolax.parser import HTMLParser


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
        'label': 'Is Terminating Version',
        'value': 'is_terminating_version'
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

clientside_callback(
    f"""
    ({{ length }}) => {{
        return [
            length / {len(review_checklist_items)} * 100,
            `${{length}} / {len(review_checklist_items)}`
        ]
    }}
    """,
    Output('document-version-review-checklist-progress-bar', 'value'),
    Output('document-version-review-checklist-progress-bar', 'label'),
    Input('document-version-review-checklist', 'value'),
    prevent_initial_call=True
)

modal_add_models = {
    'language': Language,
    'jurisdiction': Jurisdiction,
    'document-type': DocumentType
}

def document_version_add_handler_wrapper(field):
    def handler(data):
        model = modal_add_models[field]
        model.create(**data)

        return True, model.get_select_values()

    return handler

clientside_callback(
    """
    () => dash_clientside.callback_context.triggered[0].prop_id ===
          'document-version-review-checklist-button.n_clicks'
    """,
    Output('document-version-review-checklist-modal', 'is_open'),
    Input('document-version-review-checklist-modal-close-button', 'n_clicks'),
    Input('document-version-review-checklist-button', 'n_clicks'),
    prevent_initial_call=True
)

for field in ['language', 'jurisdiction', 'document-type']:
    clientside_callback(
        f"""
        (a, b, c, label, value) => {{
            const prop_id = dash_clientside.callback_context.triggered[0].prop_id
            if (prop_id === 'document-version-add-{field}-button.n_clicks') {{
                return [true, dash_clientside.no_update]
            }} else if (prop_id === 'document-version-add-{field}-modal-save-button.n_clicks') {{
                return [false, {{ label, value }}]
            }}

            return [false, dash_clientside.no_update]
        }}
        """,
        Output(f'document-version-add-{field}-modal', 'is_open'),
        Output(f'document-version-add-{field}-store', 'data'),
        Input(f'document-version-add-{field}-button', 'n_clicks'),
        Input(f'document-version-add-{field}-modal-save-button', 'n_clicks'),
        Input(f'document-version-add-{field}-modal-cancel-button', 'n_clicks'),
        State(f'document-version-add-{field}-modal-label-input', 'value'),
        State(f'document-version-add-{field}-modal-value-input', 'value'),
        prevent_initial_call=True
    )

    clientside_callback(
        """
        () => ['', '']
        """,
        Output(f'document-version-add-{field}-modal-label-input', 'value'),
        Output(f'document-version-add-{field}-modal-value-input', 'value'),
        Input(f'document-version-add-{field}-modal', 'is_open'),
        prevent_initial_call=True
    )

    callback(
        Output(f'document-version-add-{field}-toast', 'is_open'),
        Output(f'document-version-{field}', 'options'),
        Input(f'document-version-add-{field}-store', 'data'),
        prevent_initial_call=True
    )(document_version_add_handler_wrapper(field))

clientside_callback(
    """
    (a, b, c, text, color) => {
        const prop_id = dash_clientside.callback_context.triggered[0].prop_id
        if (prop_id === 'document-version-add-tag-button.n_clicks') {
            return [true, dash_clientside.no_update]
        } else if (prop_id === 'document-version-add-tag-modal-save-button.n_clicks') {
            return [false, { text, color }]
        }

        return [false, dash_clientside.no_update]
    }
    """,
    Output('document-version-add-tag-modal', 'is_open'),
    Output('document-version-add-tag-store', 'data'),
    Input('document-version-add-tag-button', 'n_clicks'),
    Input('document-version-add-tag-modal-save-button', 'n_clicks'),
    Input('document-version-add-tag-modal-cancel-button', 'n_clicks'),
    State('document-version-add-tag-modal-text-input', 'value'),
    State('document-version-add-tag-modal-color-input', 'value'),
    prevent_initial_call=True
)

clientside_callback(
    """
    () => ['', '#000000']
    """,
    Output('document-version-add-tag-modal-text-input', 'value'),
    Output('document-version-add-tag-modal-color-input', 'value'),
    Input('document-version-add-tag-modal', 'is_open'),
    prevent_initial_call=True
)

@callback(
    Output('document-version-add-tag-toast', 'is_open'),
    Output('document-version-tags', 'options'),
    Input('document-version-add-tag-store', 'data'),
    prevent_initial_call=True
)
def document_version_add_tag_handler(data):
    Tag.create(**data)
    return True, Tag.get_select_values()

clientside_callback(
    """
    (a, b, c, label, suffix, mimetype) => {
        const prop_id = dash_clientside.callback_context.triggered[0].prop_id
        if (prop_id === 'document-version-add-file-type-button.n_clicks') {
            return [true, dash_clientside.no_update]
        } else if (prop_id === 'document-version-add-file-type-modal-save-button.n_clicks') {
            return [false, { label, suffix, mimetype }]
        }

        return [false, dash_clientside.no_update]
    }
    """,
    Output('document-version-add-file-type-modal', 'is_open'),
    Output('document-version-add-file-type-store', 'data'),
    Input('document-version-add-file-type-button', 'n_clicks'),
    Input('document-version-add-file-type-modal-save-button', 'n_clicks'),
    Input('document-version-add-file-type-modal-cancel-button', 'n_clicks'),
    State('document-version-add-file-type-modal-label-input', 'value'),
    State('document-version-add-file-type-modal-suffix-input', 'value'),
    State('document-version-add-file-type-modal-mimetype-input', 'value'),
    prevent_initial_call=True
)

clientside_callback(
    """
    () => ['', '', '']
    """,
    Output('document-version-add-file-type-modal-label-input', 'value'),
    Output('document-version-add-file-type-modal-suffix-input', 'value'),
    Output('document-version-add-file-type-modal-mimetype-input', 'value'),
    Input('document-version-add-file-type-modal', 'is_open'),
    prevent_initial_call=True
)

@callback(
    Output('document-version-add-file-type-toast', 'is_open'),
    Output('document-version-file-type', 'options'),
    Input('document-version-add-file-type-store', 'data'),
    prevent_initial_call=True
)
def document_version_add_file_type_handler(data):
    FileType.create(**data)
    return True, FileType.get_select_values()

clientside_callback(
    """
    () => (
        dash_clientside.callback_context.triggered[0]?.prop_id ===
            'document-version-delete-document-button.n_clicks'
    )
    """,
    Output('document-version-delete-document-modal', 'is_open'),
    Input('document-version-delete-document-button', 'n_clicks'),
    Input('document-version-delete-document-modal-cancel-button', 'n_clicks'),
    Input('document-version-delete-document-modal-delete-button', 'n_clicks'),
    prevent_initial_call=True
)

@callback(
    Output('document-version-delete-toast', 'is_open'),
    Input('document-version-delete-document-modal-delete-button', 'n_clicks'),
    State('document-version-data-store', 'data'),
    prevent_initial_call=True
)
def document_version_delete_document_handler(_, data):
    print('deleting document', data['document_id'])
    return True

@callback(
    Output('document-version-download-file-toast', 'is_open'),
    Output('document-version-download-file', 'data'),
    Input('document-version-download-file-button', 'n_clicks'),
    State('document-version-download-file-path', 'data'),
    prevent_initial_call=True
)
def document_version_download_file_handler(_, file_path):
    return True, dcc.send_file(
        file_path
    )

@callback(
    Output('document-version-download-processed-file-toast', 'is_open'),
    Output('document-version-download-processed-file', 'data'),
    Input('document-version-download-processed-file-button', 'n_clicks'),
    State('document-version-download-processed-file-path', 'data'),
    prevent_initial_call=True
)
def document_version_download_processed_file_handler(_, file_path):
    return True, dcc.send_file(
        file_path
    )

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
        const is_terminating_version = check_boxes.includes('is_terminating_version')

        const review_checklist = review_checklist_values.reduce(
            (t, x) => ({ [x]: true, ... t}), {}
        )

        return [
            {
                ...data,
                reviewed, flagged_for_review, importance, has_relevant_information,
                is_foreign_language, is_malformed, is_empty, is_terminating_version,
                title, slug, source, source_notes, language, file_type, tags,
                jurisdictions, document_types, notes, variables, review_checklist
            },
            false
        ]
    }
    """,
    Output('document-version-data-store', 'data'),
    Output('document-version-save-button', 'disabled'),
    Input('document-version-review-switches', 'value'),
    Input('document-version-importance', 'value'),
    Input('document-version-switches', 'value'),
    Input('document-version-title', 'value'),
    Input('document-version-slug', 'value'),
    Input('document-version-source', 'value'),
    Input('document-version-source-notes', 'value'),
    Input('document-version-language', 'value'),
    Input('document-version-file-type', 'value'),
    Input('document-version-tags', 'value'),
    Input('document-version-jurisdiction', 'value'),
    Input('document-version-document-type', 'value'),
    Input('document-version-notes', 'value'),
    Input('document-version-variables', 'value'),
    Input('document-version-review-checklist', 'value'),
    State('document-version-data-store', 'data'),
    prevent_initial_call=True
)

@callback(
    Output('document-version-save-toast', 'is_open'),
    Input('document-version-save-button', 'n_clicks'),
    State('document-version-data-store', 'data'),
    prevent_initial_call=True
)
def document_version_save_handler(_, data):
    document_id = int(data.pop('document_id'))
    tags = data.pop('tags', [])
    jurisdictions = data.pop('jurisdictions', [])
    document_types = data.pop('document_types', [])
    data['variables'] = json.loads(data['variables'])

    DocumentVersion \
        .update(**data) \
        .where(DocumentVersion.id == document_id) \
        .execute()

    for field_name, values, through_table in [
        ('tag', tags, DocumentVersionTagThroughTable),
        ('jurisdiction', jurisdictions, DocumentVersionJurisdictionThroughTable),
        ('document_type', document_types, DocumentVersionDocumentTypeThroughTable)
    ]:
        through_table \
            .delete() \
            .where(through_table.document_version == document_id) \
            .execute()

        through_table \
            .insert_many([{
                'document_version': document_id,
                field_name: i
            } for i in values]) \
            .execute()
    return True

def layout(document_id=None) -> html.Div:
    if document_id is None:
        document = None
    else:
        document = DocumentVersion.get_one(
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

    database_id = getattr(document, 'id', '')
    version_num = getattr(document, 'version_num', None)
    num_versions = getattr(document, 'num_versions', None)
    document_database_id = getattr(document, 'document_id', '')

    if database_id != '':
        next_document_id = database_id + 1
        prev_document_id = database_id - 1

        next_document_url = f'/document-version/{next_document_id}'
        prev_document_url = f'/document-version/{prev_document_id}'

        next_document_disabled = False
        prev_document_disabled = False
    else:
        next_document_url = '#'
        prev_document_url = '#'

        next_document_disabled = True
        prev_document_disabled = True

    source = getattr(document, 'source', '')
    source_notes = getattr(document, 'source_notes', '')

    document_issuer = getattr(document, 'issuer', {})
    document_issuer_short_name = document_issuer.get('short_name', '')
    document_issuer_long_name = document_issuer.get('long_name', '')

    file = getattr(document, 'presentation_ready_file', '')
    processed_file = getattr(document, 'processed_file', '')
    original_file = getattr(document, 'file', '')

    processed_file_exists = getattr(
        document,
        'processed_file_exists',
        False
    )

    notes = getattr(document, 'notes', '')
    variables = json.dumps(
        getattr(document, 'variables', '')
    )

    checkbox_fields = [
        'has_relevant_information', 'is_foreign_language',
        'is_malformed', 'is_empty', 'is_terminating_version'
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
    file_type_mimetype = getattr(file_type, 'mimetype', None)

    language = getattr(document, 'language', None)
    language_value = getattr(language, 'id', None)

    tags = [t['id'] for t in getattr(document, 'tags', []) or []]
    jurisdictions = [
        t['id'] for t in getattr(document, 'jurisdictions', []) or []
    ]
    document_types = [
        t['id'] for t in getattr(document, 'types', []) or []
    ]

    if file != '':
        if file_type_mimetype == 'application/pdf':
            file_data = base64_encode_file(
                file
            )
        else:
            file_data = load_file(file)
            file_data = HTMLParser(file_data)
            for script_tag in file_data.css('script, meta[http-equiv="refresh"]'):
                script_tag.decompose()
            file_data = file_data.html

        annotator = DashAnnotator(
            data_type=file_type_mimetype,
            data=file_data,
            id='document-version-annotator'
        )
    else:
        annotator = html.Span(id='document-version-annotator')

    review_checklist = [
        i for i, v in getattr(document, 'review_checklist', {}).items() if v
    ]
    review_checklist_completed = len(review_checklist)
    review_checklist_progress = review_checklist_completed / len(review_checklist_items) * 100
    review_checklist_progress_label = f'{review_checklist_completed} / {len(review_checklist_items)}'

    return html.Div(
        [
            DashSplitPane(
                children=[
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
                                id='document-version-delete-toast',
                                style={
                                    'position': 'fixed',
                                    'top': 66,
                                    'right': 10,
                                    'width': 350
                                }
                            ),
                            dcc.Download(id='document-version-download-file'),
                            dcc.Store(
                                id='document-version-download-file-path',
                                data=original_file
                            ),
                            dcc.Download(id='document-version-download-processed-file'),
                            dcc.Store(
                                id='document-version-download-processed-file-path',
                                data=original_file
                            ),
                            dbc.Toast(
                                [
                                    html.P('The document has been saved.', className='mb-0')
                                ],
                                header='Success',
                                icon='success',
                                duration=4000,
                                is_open=False,
                                id='document-version-save-toast',
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
                                                id='document-version-delete-document-modal-delete-button'
                                            ),
                                            dbc.Button(
                                                'Cancel',
                                                color='warning',
                                                id='document-version-delete-document-modal-cancel-button'
                                            )
                                        ]
                                    ),
                                ],
                                id='document-version-delete-document-modal',
                                centered=True,
                                is_open=False,
                            ),
                            dbc.Toast(
                                [
                                    html.P('The file has been downloaded.', className='mb-0')
                                ],
                                header='Success',
                                icon='success',
                                duration=4000,
                                is_open=False,
                                id='document-version-download-file-toast',
                                style={
                                    'position': 'fixed',
                                    'top': 66,
                                    'right': 10,
                                    'width': 350
                                }
                            ),
                            dbc.Toast(
                                [
                                    html.P('The processed file has been downloaded.', className='mb-0')
                                ],
                                header='Success',
                                icon='success',
                                duration=4000,
                                is_open=False,
                                id='document-version-download-processed-file-toast',
                                style={
                                    'position': 'fixed',
                                    'top': 66,
                                    'right': 10,
                                    'width': 350
                                }
                            ),
                            dcc.Store(
                                id='document-version-data-store',
                                data={
                                    'document_id': document_id
                                }
                            ),
                            dcc.Store(
                                id='document-version-add-language-store',
                                data={}
                            ),
                            dcc.Store(
                                id='document-version-add-jurisdiction-store',
                                data={}
                            ),
                            dcc.Store(
                                id='document-version-add-document-type-store',
                                data={}
                            ),
                            dcc.Store(
                                id='document-version-add-tag-store',
                                data={}
                            ),
                            dcc.Store(
                                id='document-version-add-file-type-store',
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
                                                id='document-version-review-checklist-progress-bar'
                                            ),
                                            dbc.Checklist(
                                                options=review_checklist_items,
                                                value=review_checklist,
                                                id='document-version-review-checklist'
                                            )
                                        ]
                                    ),
                                    dbc.ModalFooter(
                                        dbc.Button(
                                            'Close',
                                            className='ms-auto',
                                            id='document-version-review-checklist-modal-close-button'
                                        )
                                    ),
                                ],
                                id='document-version-review-checklist-modal',
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
                                                            id='document-version-add-language-modal-label-input'
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
                                                            id='document-version-add-language-modal-value-input'
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
                                                id='document-version-add-language-modal-save-button'
                                            ),
                                            dbc.Button(
                                                'Cancel',
                                                color='warning',
                                                id='document-version-add-language-modal-cancel-button'
                                            )
                                        ]
                                    ),
                                ],
                                id='document-version-add-language-modal',
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
                                id='document-version-add-language-toast',
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
                                                            id='document-version-add-jurisdiction-modal-label-input'
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
                                                            id='document-version-add-jurisdiction-modal-value-input'
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
                                                id='document-version-add-jurisdiction-modal-save-button'
                                            ),
                                            dbc.Button(
                                                'Cancel',
                                                color='warning',
                                                id='document-version-add-jurisdiction-modal-cancel-button'
                                            )
                                        ]
                                    ),
                                ],
                                id='document-version-add-jurisdiction-modal',
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
                                id='document-version-add-jurisdiction-toast',
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
                                                            id='document-version-add-document-type-modal-label-input'
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
                                                            id='document-version-add-document-type-modal-value-input'
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
                                                id='document-version-add-document-type-modal-save-button'
                                            ),
                                            dbc.Button(
                                                'Cancel',
                                                color='warning',
                                                id='document-version-add-document-type-modal-cancel-button'
                                            )
                                        ]
                                    ),
                                ],
                                id='document-version-add-document-type-modal',
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
                                id='document-version-add-document-type-toast',
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
                                                            id='document-version-add-tag-modal-text-input'
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
                                                            id='document-version-add-tag-modal-color-input'
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
                                                id='document-version-add-tag-modal-save-button'
                                            ),
                                            dbc.Button(
                                                'Cancel',
                                                color='warning',
                                                id='document-version-add-tag-modal-cancel-button'
                                            )
                                        ]
                                    ),
                                ],
                                id='document-version-add-tag-modal',
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
                                id='document-version-add-tag-toast',
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
                                                            id='document-version-add-file-type-modal-label-input'
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
                                                            id='document-version-add-file-type-modal-suffix-input'
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
                                                            id='document-version-add-file-type-modal-mimetype-input'
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
                                                id='document-version-add-file-type-modal-save-button'
                                            ),
                                            dbc.Button(
                                                'Cancel',
                                                color='warning',
                                                id='document-version-add-file-type-modal-cancel-button'
                                            )
                                        ]
                                    ),
                                ],
                                id='document-version-add-file-type-modal',
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
                                id='document-version-add-file-type-toast',
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
                                                    html.I(className='bi bi-arrow-left-circle h5'),
                                                    color='secondary',
                                                    class_name='button-with-icon-no-text',
                                                    id='document-version-previous-button',
                                                    href=prev_document_url,
                                                    disabled=prev_document_disabled,
                                                    external_link=False
                                                ),
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
                                                    id='document-version-save-button'
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
                                                    id='document-version-review-checklist-button'
                                                ),
                                                dbc.DropdownMenu(
                                                    [
                                                        dbc.DropdownMenuItem(
                                                            html.Span(
                                                                [
                                                                    html.I(
                                                                        className='bi bi-file-earmark-arrow-down dropdown-menu-icon'
                                                                    ),
                                                                    html.Span('Download File')
                                                                ]
                                                            ),
                                                            id='document-version-download-file-button'
                                                        ),
                                                        dbc.DropdownMenuItem(
                                                            html.Span(
                                                                [
                                                                    html.I(
                                                                        className='bi bi-box-arrow-down dropdown-menu-icon'
                                                                    ),
                                                                    html.Span('Download Processed File')
                                                                ]
                                                            ),
                                                            id='document-version-download-processed-file-button',
                                                            disabled=not processed_file_exists
                                                        ),
                                                        dbc.DropdownMenuItem(
                                                            html.Span(
                                                                [
                                                                    html.I(
                                                                        className='bi bi-trash dropdown-menu-icon'
                                                                    ),
                                                                    html.Span('Delete Document')
                                                                ]
                                                            ),
                                                            id='document-version-delete-document-button'
                                                        )
                                                    ],
                                                    label='More',
                                                    color='warning',
                                                    group=True,
                                                ),
                                                dbc.Button(
                                                    html.I(className='bi bi-arrow-right-circle h5'),
                                                    color='secondary',
                                                    class_name='button-with-icon-no-text',
                                                    id='document-version-next-button',
                                                    href=next_document_url,
                                                    disabled=next_document_disabled,
                                                    external_link=False
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
                                                id='document-version-importance',
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
                                            id='document-version-review-switches'
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
                                                },
                                                {
                                                    'label': 'Is Terminating Version',
                                                    'value': 'is_terminating_version'
                                                }
                                            ],
                                            value=checkbox_values,
                                            inline=True,
                                            id='document-version-switches'
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
                                                id='document-version-title'
                                            )
                                        ]
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label('Document Slug'),
                                            dbc.Input(
                                                type='text',
                                                value=slug,
                                                id='document-version-slug'
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
                                            dbc.Label('Version #'),
                                            dbc.Input(
                                                type='number',
                                                value=version_num,
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
                                            dbc.Label('Document Database ID'),
                                            dbc.InputGroup(
                                                [
                                                    dbc.Input(
                                                        type='number',
                                                        value=document_database_id,
                                                        disabled=True
                                                    ),
                                                    dcc.Link(
                                                        dbc.Button(
                                                            html.I(className='bi bi-box-arrow-up-right')
                                                        ),
                                                        href=f'/document/{document_database_id}',
                                                        target='_blank'
                                                    )
                                                ]
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
                                                    id='document-version-source'
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
                                            id='document-version-source-notes'
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
                                                        id='document-version-language'
                                                    ),
                                                    dbc.Button(
                                                        html.I(className='bi bi-plus h4'),
                                                        class_name='plus-button',
                                                        id='document-version-add-language-button'
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
                                            dbc.Label('File'),
                                            dbc.Input(
                                                type='text',
                                                value=original_file,
                                                id='document-version-file',
                                                placeholder='Put file path here...',
                                                disabled=True
                                            )
                                        ]
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label('File Type'),
                                            dbc.InputGroup(
                                                [
                                                    dcc.Dropdown(
                                                        options=FileType.get_select_values(),
                                                        value=file_type_value,
                                                        id='document-version-file-type'
                                                    ),
                                                    dbc.Button(
                                                        html.I(className='bi bi-plus h4'),
                                                        class_name='plus-button',
                                                        id='document-version-add-file-type-button'
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
                                                    id='document-version-tags'
                                                ),
                                                dbc.Button(
                                                    html.I(className='bi bi-plus h4'),
                                                    class_name='plus-button',
                                                    id='document-version-add-tag-button'
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
                                                    id='document-version-jurisdiction'
                                                ),
                                                dbc.Button(
                                                    html.I(className='bi bi-plus h4'),
                                                    class_name='plus-button',
                                                    id='document-version-add-jurisdiction-button'
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
                                                    id='document-version-document-type'
                                                ),
                                                dbc.Button(
                                                    html.I(className='bi bi-plus h4'),
                                                    class_name='plus-button',
                                                    id='document-version-add-document-type-button'
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
                                            id='document-version-notes',
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
                                            id='document-version-variables',
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
                    dbc.Container(
                        annotator
                    )
                ],
                style={'height': 'calc(100% - 78px)'},
                split='vertical',
                size='50%',
            )
        ]
    )

register_page(
    module=__name__,
    path='/document-version',
    path_template='/document-version/<document_id>',
    title='Document Version',
    order=-1
)

from dash import (
    html,
    dcc,
    Output,
    Input,
    State,
    callback,
    clientside_callback,
    ALL
)
import dash_bootstrap_components as dbc

from covid19_guidance_explorer.pages import register_page
from covid19_guidance_explorer.database import (
    DocumentVersionJurisdictionThroughTable,
    DocumentJurisdictionThroughTable,
    Jurisdiction,
)


clientside_callback(
    """
    (buttonClicks) => {
        const prop_id = dash_clientside.callback_context.triggered[0]?.prop_id
        if ([
            'jurisdictions-delete-are-you-sure-modal-cancel-button.n_clicks',
            'jurisdictions-delete-are-you-sure-modal-delete-button.n_clicks'
        ].includes(prop_id)) {
            return [null, false]
        } else if (!buttonClicks.every(i => i === undefined)) {
            const { id } = parsePatternMatchingId(prop_id)
            return [id.index, true]
        }

        return [dash_clientside.no_update, false]
    }
    """,
    Output("jurisdictions-delete-store", "data"),
    Output("jurisdictions-delete-are-you-sure-modal", "is_open"),
    Input({"type": "jurisdictions-delete-button", "index": ALL}, "n_clicks"),
    Input("jurisdictions-delete-are-you-sure-modal-delete-button", "n_clicks"),
    Input("jurisdictions-delete-are-you-sure-modal-cancel-button", "n_clicks"),
    prevent_initial_call=True,
)


@callback(
    Output("jurisdictions-delete-toast", "is_open"),
    Input("jurisdictions-delete-are-you-sure-modal-delete-button", "n_clicks"),
    State("jurisdictions-delete-store", "data"),
    prevent_initial_call=True,
)
def jurisdictions_delete_handler(_, jurisdiction_id):
    DocumentJurisdictionThroughTable.delete().where(
        DocumentJurisdictionThroughTable.jurisdiction_id == jurisdiction_id
    ).execute()

    DocumentVersionJurisdictionThroughTable.delete().where(
        DocumentVersionJurisdictionThroughTable.jurisdiction_id == jurisdiction_id
    ).execute()

    Jurisdiction.delete().where(Jurisdiction.id == jurisdiction_id).execute()

    return True


clientside_callback(
    """
    (a, b, c, label, value) => {
        if (
            dash_clientside.callback_context.triggered[0]?.prop_id ===
                'jurisdictions-add-jurisdiction-modal-save-button.n_clicks'
        ) {
            return [false, { label, value }]
        }

        return [
            dash_clientside.callback_context.triggered[0]?.prop_id ===
                'jurisdictions-add-jurisdiction-button.n_clicks',
            dash_clientside.no_update
        ]
    }
    """,
    Output("jurisdictions-add-jurisdiction-modal", "is_open"),
    Output("jurisdictions-new-store", "data"),
    Input("jurisdictions-add-jurisdiction-button", "n_clicks"),
    Input("jurisdictions-add-jurisdiction-modal-save-button", "n_clicks"),
    Input("jurisdictions-add-jurisdiction-modal-cancel-button", "n_clicks"),
    State("jurisdictions-add-jurisdiction-modal-label-input", "value"),
    State("jurisdictions-add-jurisdiction-modal-value-input", "value"),
    prevent_initial_call=True,
)


@callback(
    Output("jurisdictions-new-toast", "is_open"),
    Input("jurisdictions-new-store", "data"),
    prevent_initial_call=True,
)
def jurisdictions_new_handler(data):
    Jurisdiction.create(**data)
    return True


clientside_callback(
    """
    () => ['', '']
    """,
    Output("jurisdictions-add-jurisdiction-modal-label-input", "value"),
    Output("jurisdictions-add-jurisdiction-modal-value-input", "value"),
    Input("jurisdictions-add-jurisdiction-modal", "is_open"),
)


@callback(
    Output("jurisdictions-table-pagination", "max_value"),
    Output("jurisdictions-table-container", "children"),
    Input("jurisdictions-table-search-input", "n_submit"),
    Input("jurisdictions-table-search-button", "n_clicks"),
    Input("jurisdictions-table-pagination", "active_page"),
    Input("jurisdictions-table-rows-per-page", "value"),
    Input("jurisdictions-new-store", "data"),
    Input("jurisdictions-delete-are-you-sure-modal-delete-button", "n_clicks"),
    State("jurisdictions-table-search-input", "value"),
)
def handled_table(_, __, page, rows_per_page, ___, ____, search_text):
    search_string = None if search_text == "" else search_text
    n = int(rows_per_page)

    jurisdictions = Jurisdiction.get_values(
        k=page,
        n=n,
        search_string=search_string
    )

    num_pages = Jurisdiction.get_num_pages(n=n, search_string=search_string)

    table_body = [
        html.Tr(
            [
                html.Td(jurisdiction.id),
                html.Td(jurisdiction.label),
                html.Td(jurisdiction.value),
                html.Td(
                    [
                        dbc.Button(
                            html.I(className="bi bi-trash"),
                            color="danger",
                            id={
                                "type": "jurisdictions-delete-button",
                                "index": jurisdiction.id,
                            },
                        ),
                        dbc.Tooltip(
                            "Delete jurisdiction",
                            target={
                                "type": "jurisdictions-delete-button",
                                "index": jurisdiction.id,
                            },
                            class_name="tooltip-no-arrow",
                            placement="left",
                        ),
                    ],
                    className="text-center",
                    style={"width": "70px"},
                ),
            ]
        )
        for jurisdiction in jurisdictions
    ]

    table = dbc.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Database ID", className="text-nowrap"),
                        html.Th("Label", className="text-nowrap"),
                        html.Th("Value", className="text-nowrap"),
                        html.Th("", style={"width": "70px"}),
                    ]
                )
            ),
            html.Tbody(table_body),
        ],
        bordered=True,
        style={"tableLayout": "fixed"},
    )

    return num_pages, table


clientside_callback(
    """
    () => (
        dash_clientside.callback_context.triggered[0]?.prop_id !==
            'jurisdictions-table-pagination.active_page' ? 1 :
            dash_clientside.no_update
    )
    """,
    Output("jurisdictions-table-pagination", "active_page"),
    Input("jurisdictions-table-search-input", "n_submit"),
    Input("jurisdictions-table-search-button", "n_clicks"),
    Input("jurisdictions-table-pagination", "active_page"),
    Input("jurisdictions-table-rows-per-page", "value"),
)


def layout() -> html.Div:
    return html.Div(
        [
            dbc.Toast(
                [html.P("The jurisdiction has been added.", className="mb-0")],
                header="Success",
                icon="success",
                duration=4000,
                is_open=False,
                id="jurisdictions-new-toast",
                style={
                    "position": "fixed",
                    "top": 66,
                    "right": 10,
                    "width": 350
                },
            ),
            dbc.Toast(
                [
                    html.P(
                        "The jurisdiction has been deleted.",
                        className="mb-0"
                    )
                ],
                header="Success",
                icon="success",
                duration=4000,
                is_open=False,
                id="jurisdictions-delete-toast",
                style={
                    "position": "fixed",
                    "top": 66,
                    "right": 10,
                    "width": 350
                },
            ),
            dcc.Store(id="jurisdictions-delete-store"),
            dcc.Store(id="jurisdictions-new-store"),
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle("Are you sure?"),
                        close_button=True
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Delete",
                                className="ms-auto",
                                color="danger",
                                id=(
                                    "jurisdictions-delete-are-you-"
                                    "sure-modal-delete-button"
                                ),
                            ),
                            dbc.Button(
                                "Cancel",
                                color="warning",
                                id=(
                                    "jurisdictions-delete-are-you-"
                                    "sure-modal-cancel-button"
                                ),
                            ),
                        ]
                    ),
                ],
                id="jurisdictions-delete-are-you-sure-modal",
                centered=True,
                is_open=False,
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle("Add Jurisdiction"), close_button=True
                    ),
                    dbc.ModalBody(
                        [
                            dbc.Row(
                                dbc.Col(
                                    [
                                        dbc.Label("Label"),
                                        dbc.Input(
                                            type="text",
                                            placeholder="Enter label here...",
                                            id=(
                                                "jurisdictions-add-juris"
                                                "diction-modal-label-input"
                                            ),
                                        ),
                                    ]
                                )
                            ),
                            dbc.Row(
                                dbc.Col(
                                    [
                                        dbc.Label("Value"),
                                        dbc.Input(
                                            type="text",
                                            placeholder="Enter value here...",
                                            id=(
                                                "jurisdictions-add-juris"
                                                "diction-modal-value-input"
                                            ),
                                        ),
                                    ]
                                ),
                                class_name="mt-2",
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Save",
                                className="ms-auto",
                                color="success",
                                id=(
                                    "jurisdictions-add-jurisdiction"
                                    "-modal-save-button"
                                ),
                            ),
                            dbc.Button(
                                "Cancel",
                                color="warning",
                                id="jurisdictions-add-jurisdiction-modal-cancel-button",
                            ),
                        ]
                    ),
                ],
                id="jurisdictions-add-jurisdiction-modal",
                centered=True,
                is_open=False,
            ),
            dbc.Row(
                [
                    dbc.Col(html.H1("Jurisdictions", className="h3"), width=5),
                    dbc.Col(
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Button(
                                        html.Div(
                                            [
                                                html.I(className="bi bi-plus-lg h5"),
                                                html.Span("Add Jurisdiction"),
                                            ]
                                        ),
                                        color="info",
                                        class_name="button-with-icon",
                                        id="jurisdictions-add-jurisdiction-button",
                                        style={"padding": "5.09px 12px"},
                                    ),
                                    style={"textAlign": "right"},
                                    width="auto",
                                ),
                                dbc.Col(
                                    dbc.InputGroup(
                                        [
                                            dbc.InputGroupText(
                                                html.I(
                                                    className="bi bi-search"
                                                )
                                            ),
                                            dbc.Input(
                                                value="",
                                                placeholder="Search...",
                                                id="jurisdictions-table-search-input",
                                            ),
                                            dbc.Button(
                                                "Search",
                                                id="jurisdictions-table-search-button",
                                            ),
                                        ],
                                        class_name="p-0",
                                    )
                                ),
                            ],
                            class_name="g-3",
                        ),
                        width={"size": 6, "offset": 1},
                    ),
                ],
                class_name="mb-1",
            ),
            dcc.Loading(id="jurisdictions-table-container", className="table-loader"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Rows per page", class_name="small mb-0"),
                            dbc.Select(
                                options=[
                                    {"label": i, "value": i} for i in range(1, 11)
                                ],
                                id="jurisdictions-table-rows-per-page",
                                value=5,
                            ),
                        ],
                        width=2,
                        style={"position": "relative", "bottom": "10px"},
                    ),
                    dbc.Col(
                        dbc.Pagination(
                            active_page=1,
                            max_value=1,
                            fully_expanded=False,
                            previous_next=True,
                            first_last=True,
                            style={"float": "right"},
                            id="jurisdictions-table-pagination",
                        ),
                        width=10,
                    ),
                ]
            ),
        ]
    )


register_page(
    module=__name__,
    path="/jurisdictions",
    title="Jurisdictions",
    order=5,
    icon="map-fill",
)

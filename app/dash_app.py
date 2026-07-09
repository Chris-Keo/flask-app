import json
import os
import sys
import urllib.request
from typing import Any

APP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(APP_DIR)
if APP_DIR in sys.path:
    sys.path.remove(APP_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
import dash
import dash_bootstrap_components as dbc
import psycopg2
import redis
import uvicorn
from dash import Dash, Input, Output, State, ALL, callback, dcc, html
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from psycopg2.extras import Json, RealDictCursor


DB_CONFIG: dict[str, Any] = {
    "host": os.getenv("PGHOST", "chriskeodata"),
    "port": int(os.getenv("PGPORT", "5432")),
    "user": os.getenv("PGUSER", "christsnakeo"),
    "password": os.getenv("PGPASSWORD", "Abletonlive44!"),
    "dbname": os.getenv("PGDATABASE", "flask_app_db"),
}
DEFAULT_AUDIT_USER = os.getenv("AUDIT_USER", os.getenv("PGUSER", "dash_user"))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_CHANNEL = os.getenv("REDIS_CHANNEL", "flask-app-events")
REDIS_EVENTS_KEY = f"{REDIS_CHANNEL}:list"
EVENT_STORE: list[dict[str, Any]] = []

try:
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
except Exception:
    redis_client = None

FASTAPI_APP = FastAPI(title="Flask App Events")


def publish_event(action: str, table_name: str, row_id: int | None, payload: dict[str, Any] | None = None, changed_by: str | None = None) -> dict[str, Any]:
    event = {
        "action": action,
        "table_name": table_name,
        "row_id": row_id,
        "payload": payload or {},
        "changed_by": changed_by or DEFAULT_AUDIT_USER,
    }
    EVENT_STORE.append(event)
    EVENT_STORE[:] = EVENT_STORE[-50:]

    if redis_client is not None:
        try:
            redis_client.publish(REDIS_CHANNEL, json.dumps(event))
            redis_client.lpush(REDIS_EVENTS_KEY, json.dumps(event))
            redis_client.ltrim(REDIS_EVENTS_KEY, 0, 49)
        except Exception as exc:
            print(f"Redis publish error: {exc}")
    return event


def get_recent_events(limit: int = 10) -> list[dict[str, Any]]:
    if redis_client is not None:
        try:
            raw_items = redis_client.lrange(REDIS_EVENTS_KEY, 0, limit - 1)
            items = [json.loads(item) for item in raw_items if item]
            if items:
                return items
        except Exception as exc:
            print(f"Redis read error: {exc}")
    return list(EVENT_STORE[-limit:])


def clear_event_log() -> None:
    EVENT_STORE.clear()
    if redis_client is not None:
        try:
            redis_client.delete(REDIS_EVENTS_KEY)
        except Exception as exc:
            print(f"Redis clear error: {exc}")


@FASTAPI_APP.get("/health")
def health_check() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@FASTAPI_APP.get("/events")
def events_endpoint(limit: int = 10) -> JSONResponse:
    return JSONResponse(get_recent_events(limit=limit))


def get_connection():
    hosts = []
    primary_host = os.getenv("PGHOST", "chriskeodata")
    if primary_host:
        hosts.append(primary_host)
    if primary_host != "localhost":
        hosts.append("localhost")
    if primary_host != "127.0.0.1":
        hosts.append("127.0.0.1")

    last_error: Exception | None = None
    for host in hosts:
        try:
            config = dict(DB_CONFIG)
            config["host"] = host
            return psycopg2.connect(**config)
        except Exception as exc:
            last_error = exc

    if last_error is not None:
        raise last_error
    raise RuntimeError("Unable to connect to PostgreSQL")


def ensure_schema() -> None:
    statements = [
        "ALTER TABLE employees ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'active'",
        "ALTER TABLE employees ADD COLUMN IF NOT EXISTS owner VARCHAR(100)",
        "ALTER TABLE employees ADD COLUMN IF NOT EXISTS budget NUMERIC(12, 2) DEFAULT 0",
        "ALTER TABLE employees ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP",
        "ALTER TABLE employees ADD COLUMN IF NOT EXISTS updated_by VARCHAR(100)",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS updated_by VARCHAR(100)",
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            id SERIAL PRIMARY KEY,
            table_name VARCHAR(100) NOT NULL,
            row_id INTEGER NOT NULL,
            action VARCHAR(20) NOT NULL,
            changed_by VARCHAR(100),
            changed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            old_values JSONB,
            new_values JSONB
        )
        """,
    ]

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                for statement in statements:
                    cur.execute(statement)
            conn.commit()
    except Exception as exc:
        print(f"Schema setup error: {exc}")


def fetch_table_rows(table_name: str) -> list[dict[str, Any]]:
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"SELECT * FROM {table_name} ORDER BY id")
                return [dict(row) for row in cur.fetchall()]
    except Exception as exc:
        print(f"Database read error for {table_name}: {exc}")
        return []


def fetch_row(table_name: str, row_id: int) -> dict[str, Any]:
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"SELECT * FROM {table_name} WHERE id = %s", (row_id,))
                row = cur.fetchone()
                return dict(row) if row else {}
    except Exception as exc:
        print(f"Database fetch error for {table_name} {row_id}: {exc}")
        return {}


def serialize_for_json(value: Any) -> Any:
    from datetime import datetime, date
    from decimal import Decimal

    if isinstance(value, dict):
        return {k: serialize_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [serialize_for_json(v) for v in value]
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "to_python"):
        return value.to_python()
    if hasattr(value, "__dict__") and not isinstance(value, (str, int, float, bool, type(None))):
        return str(value)
    return value


def log_audit_change(table_name: str, row_id: int, changed_by: str, old_values: dict[str, Any], new_values: dict[str, Any]) -> None:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO audit_log (table_name, row_id, action, changed_by, old_values, new_values)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        table_name,
                        row_id,
                        "UPDATE",
                        changed_by,
                        Json(serialize_for_json(old_values)),
                        Json(serialize_for_json(new_values)),
                    ),
                )
                conn.commit()
    except Exception as exc:
        print(f"Audit log error for {table_name} {row_id}: {exc}")


def fetch_audit_rows(table_name: str, row_id: int) -> list[dict[str, Any]]:
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, table_name, row_id, action, changed_by, changed_at, old_values, new_values
                    FROM audit_log
                    WHERE table_name = %s AND row_id = %s
                    ORDER BY changed_at DESC, id DESC
                    """,
                    (table_name, row_id),
                )
                return [dict(row) for row in cur.fetchall()]
    except Exception as exc:
        print(f"Audit fetch error for {table_name} {row_id}: {exc}")
        return []


def insert_row(table_name: str, payload: dict[str, Any], changed_by: str | None = None) -> int | None:
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                columns = list(payload.keys())
                placeholders = ", ".join(["%s"] * len(columns))
                query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders}) RETURNING id"
                cur.execute(query, list(payload.values()))
                row = cur.fetchone()
                row_id = int(row["id"]) if row and row.get("id") is not None else None
                conn.commit()
                if row_id is not None:
                    cur.execute(f"SELECT * FROM {table_name} WHERE id = %s", (row_id,))
                    new_row = dict(cur.fetchone() or {})
                    log_audit_change(table_name, row_id, changed_by or DEFAULT_AUDIT_USER, {}, new_row)
                return row_id
    except Exception as exc:
        print(f"Database insert error for {table_name}: {exc}")
        return None


def update_row(table_name: str, row_id: int, payload: dict[str, Any], changed_by: str | None = None) -> bool:
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"SELECT * FROM {table_name} WHERE id = %s", (row_id,))
                old_row = dict(cur.fetchone() or {})

                safe_payload = {k: v for k, v in payload.items() if k not in {"updated_at", "updated_by"}}
                assignments = [f"{field} = %s" for field in safe_payload.keys()]
                values = list(safe_payload.values())
                assignments.append("updated_at = CURRENT_TIMESTAMP")
                assignments.append("updated_by = %s")
                values.append(changed_by or DEFAULT_AUDIT_USER)
                values.append(row_id)

                query = f"UPDATE {table_name} SET {', '.join(assignments)} WHERE id = %s"
                cur.execute(query, values)
                conn.commit()

                cur.execute(f"SELECT * FROM {table_name} WHERE id = %s", (row_id,))
                new_row = dict(cur.fetchone() or {})

                log_audit_change(table_name, row_id, changed_by or DEFAULT_AUDIT_USER, old_row, new_row)
        return True
    except Exception as exc:
        print(f"Database update error for {table_name} {row_id}: {exc}")
        return False


def delete_row(table_name: str, row_id: int, changed_by: str | None = None) -> bool:
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"SELECT * FROM {table_name} WHERE id = %s", (row_id,))
                old_row = dict(cur.fetchone() or {})
                cur.execute(f"DELETE FROM {table_name} WHERE id = %s", (row_id,))
                conn.commit()
                log_audit_change(table_name, row_id, changed_by or DEFAULT_AUDIT_USER, old_row, {})
        return True
    except Exception as exc:
        print(f"Database delete error for {table_name} {row_id}: {exc}")
        return False


def render_table(table_name: str, rows: list[dict[str, Any]]) -> html.Div:
    if table_name == "employees":
        columns = ["id", "name", "department", "salary", "email", "status", "owner", "budget"]
        title = "Employees"
    else:
        columns = ["id", "name", "status", "owner", "budget"]
        title = "Projects"

    table_rows = []
    for row in rows:
        cells = []
        for column in columns:
            value = row.get(column, "")
            if isinstance(value, float):
                value = f"{value:,.2f}"
            cells.append(html.Td(str(value)))
        cells.append(
            html.Td(
                html.Button(
                    "Edit",
                    id={"type": "edit-button", "table": table_name, "row_id": row.get("id")},
                    n_clicks=0,
                    className="btn btn-sm btn-outline-primary",
                )
            )
        )
        table_rows.append(html.Tr(cells))

    header_cells = [html.Th(col.replace("_", " ").title()) for col in columns] + [html.Th("Action")]

    return html.Div(
        [
            html.H4(title, className="mt-3"),
            html.Table(
                [
                    html.Thead(html.Tr(header_cells)),
                    html.Tbody(table_rows),
                ],
                className="table table-striped table-sm w-100",
            ),
        ],
        className="mb-4",
    )


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "PostgreSQL Dash Editor"

ensure_schema()
initial_employees = fetch_table_rows("employees")
initial_projects = fetch_table_rows("projects")

app.layout = html.Div(
    [
        dbc.Container(
            [
                html.H2("PostgreSQL Dash Editor", className="mb-3"),
                html.P(
                    "This dashboard connects to your PostgreSQL database and opens update modals for your tables.",
                    className="text-muted",
                ),
                html.Div(
                    [
                        dbc.Button("Create Employee", id="create-employee-btn", color="success", className="me-2", n_clicks=0),
                        dbc.Button("Create Project", id="create-project-btn", color="success", n_clicks=0),
                    ],
                    className="mb-3",
                ),
                html.Div(id="status-message", className="alert alert-info", style={"display": "none"}),
                dcc.Interval(id="status-clearer", interval=5000, n_intervals=0),
                dcc.Interval(id="event-refresh", interval=3000, n_intervals=0),
                dcc.Store(id="status-timer", data=0),
                html.Div(id="employee-table", children=render_table("employees", initial_employees)),
                html.Div(id="project-table", children=render_table("projects", initial_projects)),
                dcc.Store(id="modal-state", data={"table": None, "row_id": None, "mode": "edit", "values": {}}),
                dcc.Store(id="delete-state", data={"table": None, "row_id": None}),
                html.Div(id="history-panel", className="mt-4 p-3 border rounded", style={"backgroundColor": "#f8f9fa"}),
                html.Div(id="event-feed", className="mt-4 p-3 border rounded", style={"backgroundColor": "#f8f9fa"}),
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle(id="modal-title", children="Edit Record")),
                        dbc.ModalBody(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(dbc.Label("Name"), width=6),
                                        dbc.Col(dbc.Input(id="modal-name", type="text"), width=6),
                                    ],
                                    className="mb-3",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(dbc.Label("Department"), width=6),
                                        dbc.Col(dbc.Input(id="modal-department", type="text"), width=6),
                                    ],
                                    className="mb-3",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(dbc.Label("Salary"), width=6),
                                        dbc.Col(dbc.Input(id="modal-salary", type="number"), width=6),
                                    ],
                                    className="mb-3",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(dbc.Label("Email"), width=6),
                                        dbc.Col(dbc.Input(id="modal-email", type="email"), width=6),
                                    ],
                                    className="mb-3",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(dbc.Label("Status"), width=6),
                                        dbc.Col(dbc.Input(id="modal-status", type="text"), width=6),
                                    ],
                                    className="mb-3",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(dbc.Label("Owner"), width=6),
                                        dbc.Col(dbc.Input(id="modal-owner", type="text"), width=6),
                                    ],
                                    className="mb-3",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(dbc.Label("Budget"), width=6),
                                        dbc.Col(dbc.Input(id="modal-budget", type="number"), width=6),
                                    ],
                                    className="mb-3",
                                ),
                            ]
                        ),
                        dbc.ModalFooter(
                            [
                                dbc.Button("Delete", id="delete-button", color="danger", outline=True, n_clicks=0),
                                dbc.Button("Close", id="modal-close", className="btn btn-secondary", n_clicks=0),
                                dbc.Button("Save", id="modal-submit", color="primary", n_clicks=0),
                            ]
                        ),
                    ],
                    id="edit-modal",
                    is_open=False,
                ),
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Confirm Delete")),
                        dbc.ModalBody("Are you sure you want to delete this record?"),
                        dbc.ModalFooter(
                            [
                                dbc.Button("Cancel", id="delete-cancel", className="btn btn-secondary", n_clicks=0),
                                dbc.Button("Delete", id="delete-confirm", color="danger", n_clicks=0),
                            ]
                        ),
                    ],
                    id="delete-confirm-modal",
                    is_open=False,
                ),
            ],
            fluid=True,
        )
    ],
    style={"padding": "2rem"},
)


@app.callback(
    Output("modal-state", "data", allow_duplicate=True),
    Output("edit-modal", "is_open", allow_duplicate=True),
    Output("modal-title", "children", allow_duplicate=True),
    Input({"type": "edit-button", "table": ALL, "row_id": ALL}, "n_clicks"),
    prevent_initial_call=True,
    allow_duplicate=True,
)
def open_modal(n_clicks):
    ctx = dash.callback_context
    if not ctx.triggered_id:
        return {"table": None, "row_id": None, "mode": "edit", "values": {}}, False, "Edit Record"

    table_name = ctx.triggered_id["table"]
    row_id = ctx.triggered_id["row_id"]
    row = fetch_row(table_name, row_id)

    values = {
        "name": row.get("name", ""),
        "department": row.get("department", ""),
        "salary": row.get("salary", ""),
        "email": row.get("email", ""),
        "status": row.get("status", ""),
        "owner": row.get("owner", ""),
        "budget": row.get("budget", ""),
    }
    return {"table": table_name, "row_id": row_id, "mode": "edit", "values": values}, True, f"Edit {table_name.title()} #{row_id}"


@app.callback(
    Output("modal-state", "data", allow_duplicate=True),
    Output("edit-modal", "is_open", allow_duplicate=True),
    Output("modal-title", "children", allow_duplicate=True),
    Input("create-employee-btn", "n_clicks"),
    Input("create-project-btn", "n_clicks"),
    prevent_initial_call=True,
    allow_duplicate=True,
)
def open_create_modal(employee_clicks, project_clicks):
    ctx = dash.callback_context
    if not ctx.triggered_id:
        return {"table": None, "row_id": None, "mode": "edit", "values": {}}, False, "Edit Record"

    if ctx.triggered_id == "create-employee-btn":
        table_name = "employees"
    else:
        table_name = "projects"

    values = {
        "name": "",
        "department": "",
        "salary": "",
        "email": "",
        "status": "active",
        "owner": "",
        "budget": "",
    }
    return {"table": table_name, "row_id": None, "mode": "create", "values": values}, True, f"Create {table_name.title()}"


@app.callback(
    Output("modal-name", "value"),
    Output("modal-department", "value"),
    Output("modal-salary", "value"),
    Output("modal-email", "value"),
    Output("modal-status", "value"),
    Output("modal-owner", "value"),
    Output("modal-budget", "value"),
    Output("history-panel", "children"),
    Input("modal-state", "data"),
)
def populate_modal_fields(state: dict[str, Any]):
    values = state.get("values", {}) if state else {}
    table_name = state.get("table") if state else None
    row_id = state.get("row_id") if state else None
    history_rows = fetch_audit_rows(table_name, row_id) if table_name and row_id else []

    history_children = [html.H5("Change History", className="mb-3")]
    if history_rows:
        for row in history_rows:
            history_children.append(
                html.Div(
                    [
                        html.Div(f"{row.get('changed_at')} — {row.get('changed_by') or 'unknown'}"),
                        html.Small(f"Action: {row.get('action')}"),
                    ],
                    className="mb-2 p-2 border rounded",
                )
            )
    else:
        history_children.append(html.Div("No history yet for this record.", className="text-muted"))

    return (
        values.get("name", ""),
        values.get("department", ""),
        values.get("salary", ""),
        values.get("email", ""),
        values.get("status", ""),
        values.get("owner", ""),
        values.get("budget", ""),
        history_children,
    )


@app.callback(
    Output("edit-modal", "is_open", allow_duplicate=True),
    Output("employee-table", "children", allow_duplicate=True),
    Output("project-table", "children", allow_duplicate=True),
    Output("status-message", "children", allow_duplicate=True),
    Output("status-message", "style", allow_duplicate=True),
    Output("status-timer", "data", allow_duplicate=True),
    Input("modal-submit", "n_clicks"),
    Input("modal-close", "n_clicks"),
    State("modal-state", "data"),
    State("modal-name", "value"),
    State("modal-department", "value"),
    State("modal-salary", "value"),
    State("modal-email", "value"),
    State("modal-status", "value"),
    State("modal-owner", "value"),
    State("modal-budget", "value"),
    prevent_initial_call="initial_duplicate",
    allow_duplicate=True,
)

def save_modal_changes(submit_clicks, close_clicks, modal_state, name, department, salary, email, status, owner, budget):
    try:
        ctx = dash.callback_context
        triggered_id = ctx.triggered_id if hasattr(ctx, "triggered_id") else None
    except Exception:
        triggered_id = None

    if not triggered_id:
        return False, dash.no_update, dash.no_update, "", {"display": "none"}, 0

    if triggered_id == "modal-close":
        return False, dash.no_update, dash.no_update, "", {"display": "none"}, 0

    table_name = modal_state.get("table") if modal_state else None
    row_id = modal_state.get("row_id") if modal_state else None
    mode = modal_state.get("mode", "edit") if modal_state else "edit"
    if not table_name:
        return False, dash.no_update, dash.no_update, "No row selected", {"display": "block", "padding": "1rem"}, 0

    payload: dict[str, Any] = {}
    if table_name == "employees":
        payload = {
            "name": name or "",
            "department": department or "",
            "salary": float(salary) if salary not in [None, ""] else 0.0,
            "email": email or "",
            "status": status or "active",
            "owner": owner or "",
            "budget": float(budget) if budget not in [None, ""] else 0.0,
        }
    elif table_name == "projects":
        payload = {
            "name": name or "",
            "status": status or "",
            "owner": owner or "",
            "budget": float(budget) if budget not in [None, ""] else 0.0,
        }

    if mode == "create":
        new_row_id = insert_row(table_name, payload, changed_by=DEFAULT_AUDIT_USER)
        if new_row_id is not None:
            publish_event("created", table_name, new_row_id, payload, changed_by=DEFAULT_AUDIT_USER)
            employees = fetch_table_rows("employees")
            projects = fetch_table_rows("projects")
            message = f"Created {table_name} row #{new_row_id}."
            return (
                False,
                render_table("employees", employees),
                render_table("projects", projects),
                message,
                {"display": "block", "padding": "1rem"},
                1,
            )
        return False, dash.no_update, dash.no_update, "Create failed", {"display": "block", "padding": "1rem"}, 0

    if update_row(table_name, row_id, payload, changed_by=DEFAULT_AUDIT_USER):
        publish_event("updated", table_name, row_id, payload, changed_by=DEFAULT_AUDIT_USER)
        employees = fetch_table_rows("employees")
        projects = fetch_table_rows("projects")
        message = f"Updated {table_name} row #{row_id}."
        return (
            False,
            render_table("employees", employees),
            render_table("projects", projects),
            message,
            {"display": "block", "padding": "1rem"},
            1,
        )

    return False, dash.no_update, dash.no_update, "Update failed", {"display": "block", "padding": "1rem"}, 0


@app.callback(
    Output("delete-confirm-modal", "is_open", allow_duplicate=True),
    Output("delete-state", "data"),
    Input("delete-button", "n_clicks"),
    State("modal-state", "data"),
    prevent_initial_call=True,
)
def open_delete_confirm(_n, modal_state):
    table_name = modal_state.get("table") if modal_state else None
    row_id = modal_state.get("row_id") if modal_state else None
    if not table_name or row_id is None:
        return False, {"table": None, "row_id": None}
    return True, {"table": table_name, "row_id": row_id}


@app.callback(
    Output("delete-confirm-modal", "is_open"),
    Output("edit-modal", "is_open", allow_duplicate=True),
    Output("employee-table", "children", allow_duplicate=True),
    Output("project-table", "children", allow_duplicate=True),
    Output("status-message", "children", allow_duplicate=True),
    Output("status-message", "style", allow_duplicate=True),
    Output("status-timer", "data", allow_duplicate=True),
    Input("delete-confirm", "n_clicks"),
    Input("delete-cancel", "n_clicks"),
    State("delete-state", "data"),
    prevent_initial_call=True,
    allow_duplicate=True,
)
def handle_delete(confirm_clicks, cancel_clicks, delete_state):
    ctx = dash.callback_context
    if not ctx.triggered_id:
        return False, True, dash.no_update, dash.no_update, "", {"display": "none"}, 0

    if ctx.triggered_id == "delete-cancel":
        return False, True, dash.no_update, dash.no_update, "", {"display": "none"}, 0

    table_name = delete_state.get("table") if delete_state else None
    row_id = delete_state.get("row_id") if delete_state else None
    if not table_name or row_id is None:
        return False, False, dash.no_update, dash.no_update, "No record selected", {"display": "block", "padding": "1rem"}, 0

    if delete_row(table_name, row_id, changed_by=DEFAULT_AUDIT_USER):
        publish_event("deleted", table_name, row_id, {}, changed_by=DEFAULT_AUDIT_USER)
        employees = fetch_table_rows("employees")
        projects = fetch_table_rows("projects")
        return False, False, render_table("employees", employees), render_table("projects", projects), f"Deleted {table_name} row #{row_id}.", {"display": "block", "padding": "1rem"}, 1

    return False, False, dash.no_update, dash.no_update, "Delete failed", {"display": "block", "padding": "1rem"}, 0


@app.callback(
    Output("status-message", "children"),
    Output("status-message", "style"),
    Output("status-timer", "data"),
    Input("status-clearer", "n_intervals"),
    State("status-timer", "data"),
    prevent_initial_call=True,
    allow_duplicate=True,
)
def clear_status_message(_n, status_timer):
    if not status_timer:
        return dash.no_update, dash.no_update, 0
    return "", {"display": "none"}, 0


@app.callback(
    Output("event-feed", "children"),
    Input("event-refresh", "n_intervals"),
)
def refresh_event_feed(_n):
    data = get_recent_events(limit=5)

    if not data:
        return [html.H5("Live Events"), html.Div("No events yet.", className="text-muted")]

    event_items = []
    for event in data:
        event_items.append(
            html.Div(
                [
                    html.Div(
                        f"{event.get('action', 'event').title()} — {event.get('table_name', 'unknown')} #{event.get('row_id', '?')}",
                        className="fw-bold",
                    ),
                    html.Small(f"by {event.get('changed_by', 'unknown')}"),
                ],
                className="mb-2 p-2 border rounded",
            )
        )
    return [html.H5("Live Events"), *event_items]


if __name__ == "__main__":
    app.run(debug=True)


def run_api(host: str = "0.0.0.0", port: int = 8000) -> None:
    uvicorn.run(FASTAPI_APP, host=host, port=port)

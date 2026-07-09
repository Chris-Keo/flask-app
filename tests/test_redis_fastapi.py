from app.dash_app import clear_event_log, get_recent_events, publish_event


def test_publish_event_is_recorded_and_readable():
    clear_event_log()

    event = publish_event(
        action="updated",
        table_name="employees",
        row_id=42,
        payload={"name": "Ada"},
        changed_by="tester",
    )

    assert event["action"] == "updated"
    assert event["table_name"] == "employees"
    assert event["row_id"] == 42
    assert event["payload"]["name"] == "Ada"

    recent = get_recent_events(limit=5)
    assert len(recent) == 1
    assert recent[0]["row_id"] == 42

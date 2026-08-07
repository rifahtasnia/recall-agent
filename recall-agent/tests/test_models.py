from app.db.models import Base


def test_core_database_tables_are_registered() -> None:
    assert set(Base.metadata.tables) == {
        "agent_logs",
        "businesses",
        "customers",
        "reminders",
        "service_records",
        "service_types",
    }

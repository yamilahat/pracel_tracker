from app.db.base import Base
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex


def test_gmail_ingestion_tables_are_registered() -> None:
    expected_tables = {
        "users",
        "oauth_tokens",
        "emails",
        "gmail_sync_state",
    }

    assert expected_tables.issubset(Base.metadata.tables)


def test_emails_table_does_not_store_raw_email_content() -> None:
    emails_table = Base.metadata.tables["emails"]
    forbidden_columns = {
        "body",
        "raw_body",
        "html",
        "raw_html",
        "mime_payload",
        "raw_payload",
        "headers",
        "full_headers",
    }

    assert forbidden_columns.isdisjoint(emails_table.columns.keys())


def test_expected_unique_constraints_exist() -> None:
    users_table = Base.metadata.tables["users"]
    oauth_tokens_table = Base.metadata.tables["oauth_tokens"]
    emails_table = Base.metadata.tables["emails"]
    gmail_sync_state_table = Base.metadata.tables["gmail_sync_state"]

    assert any(
        constraint.name == "uq_oauth_tokens_user_provider"
        for constraint in oauth_tokens_table.constraints
    )
    assert any(
        constraint.name == "uq_emails_user_gmail"
        for constraint in emails_table.constraints
    )
    assert any(
        constraint.name == "uq_gmail_sync_state_user_id"
        for constraint in gmail_sync_state_table.constraints
    )
    assert any(
        {"email"} == {column.name for column in constraint.columns}
        for constraint in users_table.constraints
        if hasattr(constraint, "columns")
    )


def test_email_received_indexes_exist() -> None:
    emails_table = Base.metadata.tables["emails"]
    indexes = {index.name: index for index in emails_table.indexes}

    assert "idx_emails_received" in indexes
    assert "idx_emails_user_received" in indexes

    compiled_received_index = str(
        CreateIndex(indexes["idx_emails_received"]).compile(
            dialect=postgresql.dialect(),
        )
    )

    assert "received_at DESC" in compiled_received_index

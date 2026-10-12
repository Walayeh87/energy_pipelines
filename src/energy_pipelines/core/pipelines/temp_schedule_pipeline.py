from energy_pipelines.core.database.connection import create_db_engine, create_db_session


def upsert_temp_schedule() -> None:
    db_engine = create_db_engine()
    session = create_db_session(db_engine=db_engine)

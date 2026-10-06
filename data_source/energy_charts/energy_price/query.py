import re
from typing import LiteralString, cast


def create_upsert_sql_query(
    schema_name: str,
    table_name: str,
    table_cols: list[str],
    on_conflict_cols: list[str],
    do_update_col: str,
) -> LiteralString:
    _validate_identifiers(names=schema_name)
    _validate_identifiers(names=table_name)
    _validate_identifiers(names=table_cols)
    _validate_identifiers(names=on_conflict_cols)
    _validate_identifiers(names=do_update_col)

    table_cols_as_str = ", ".join(table_cols)
    on_conflict_cols_as_str = ", ".join(on_conflict_cols)
    values = ",".join(["%s"] * len(table_cols))

    sql_query = f"""
    INSERT INTO {schema_name}.{table_name} ({table_cols_as_str})
    VALUES ({values})
    ON CONFLICT ({on_conflict_cols_as_str})
    DO UPDATE SET {do_update_col} = EXCLUDED.{do_update_col};
    """

    return cast(LiteralString, sql_query)


def _validate_identifiers(names: list[str] | str) -> None:
    alphanumeric_and_underscore = r"[a-zA-Z][a-zA-Z0-9_]*"
    if isinstance(names, str):
        names = [names]

    for col in names:
        if not re.fullmatch(alphanumeric_and_underscore, col):
            raise ValueError(f"Invalid identifier name: '{col}'")

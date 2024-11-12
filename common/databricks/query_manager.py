import copy
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from logging import Logger
from typing import Any, Optional

from pyspark.sql import types as st

import more_itertools
from databricks import sql
from databricks.sql.client import Connection, Row
from databricks.sql.exc import DatabaseError, ServerOperationError

from databricks_token_provider import DatabricksTokenProvider


SERVER_OPERATION_ERROR_MESSAGES = {
    "Table or view not found",
    "TABLE_OR_VIEW_NOT_FOUND",
}


@dataclass
class QueryManagerConfig:
    hostname: str
    http_path: str
    token_provider: DatabricksTokenProvider
    logger: Logger


class QueryManager:
    _update_queue: dict = {}

    def __init__(self, config: QueryManagerConfig = None):
        self.config = config
        self._connection: Optional[Connection] = None

    def _get_connection(self, force_new_connection: bool = False) -> Connection:
        if (
            self._connection is None
            or self.config.token_provider.is_expiring()
            or force_new_connection
        ):
            self._connection = sql.connect(
                server_hostname=self.config.hostname,
                http_path=self.config.http_path,
                access_token=self.config.token_provider.get_token(),
            )
        return self._connection

    def execute_update(self, query: str) -> None:
        def _update_execution():
            with self._get_connection().cursor() as cursor:
                cursor.execute(query)

        try:
            _update_execution()
        except Exception:
            self._get_connection(force_new_connection=True)
            _update_execution()

    def execute_query(self, query: str) -> list[Row]:
        def _execution() -> list[Row]:
            with self._get_connection().cursor() as cursor:
                cursor.execute(query)
                try:
                    return cursor.fetchall()
                except TypeError:
                    return []

        try:
            return _execution()
        except Exception:
            self._get_connection(force_new_connection=True)
            return _execution()

    def close(self):
        try:
            self._get_connection().close()
        except DatabaseError as exc:
            if "Invalid SessionHandle" not in exc.message:
                raise exc

    def _transform(self, value):
        if isinstance(value, (datetime, date)):
            result = f"'{value.isoformat()}'"
        elif isinstance(value, list):
            inner = ', '.join([self._transform(x) for x in value])
            result = f"ARRAY({inner})"
        elif isinstance(value, dict):
            inner = ", ".join(
                [f"'{k}', " + self._transform(v) for k, v in value.items()]
            )
            result = f"MAP({inner})"
        elif is_dataclass(value):
            inner = ", ".join(
                [
                    f"'{field.name}', " + self._transform(getattr(value, field.name))
                    for field in fields(value)
                ]
            )
            result = f"named_struct({inner})"
        elif isinstance(value, str):
            escaped = value.replace("'", r"\'")
            result = f"'{escaped}'"
        elif isinstance(value, Decimal):
            result = f"'{value}'"
        else:
            result = f"{value}"

        return result

    def table_or_view_exists(self, database: str, table_name: str) -> bool:
        query = f"DESCRIBE TABLE {database}.{table_name}"
        try:
            self.execute_update(query)
            return True
        except ServerOperationError as exc:
            if exc.message and any(
                message in exc.message for message in SERVER_OPERATION_ERROR_MESSAGES
            ):
                return False
            raise

    def catalog_exists(self, catalog: str) -> bool:
        query = f"DESCRIBE CATALOG {catalog}"
        try:
            self.execute_update(query)
            return True
        except ServerOperationError as error:
            if error.message and any(
                message in error.message for message in SERVER_OPERATION_ERROR_MESSAGES
            ):
                return False
            raise

    @classmethod
    def queue_for_update(
        cls,
        database: str,
        table_name: str,
        records: list,
    ) -> None:
        cls._update_queue.setdefault(
            f"{database}.{table_name}", []
        ).extend(records)

    def process_update_queue(self) -> None:
        for (
            db_table,
            records_to_persist,
        ) in QueryManager._update_queue.items():
            database, table_name = db_table.split(".")
            self.append_to_table(database, table_name, records_to_persist)
        QueryManager._update_queue.clear()

    def append_to_table(
        self,
        database: str,
        table: str,
        records: list,
    ) -> None:
        # Convert dataclasses to list of dicts
        records_copy = copy.deepcopy(records)
        records_copy = [vars(r) for r in records_copy]

        # Get list of column names from dataclass
        columns = ", ".join(records_copy[0])

        # Convert values to strings - uses iso format for dates/datetimes
        for record in records_copy:
            for k, v in record.items():
                record[k] = self._transform(v)

        for sublist in more_itertools.chunked(records_copy, 200):
            values = "), (".join([", ".join(list(record.values())) for record in sublist])
            query = f"INSERT INTO {database}.{table} ({columns}) VALUES ({values});"
            query = query.replace("'None'", "null").replace("None", "null")
            # log statement helps recreate test data required to investigate issues
            self._log(query)
            self.execute_update(query)

    def get_table(
        self,
        *,
        catalog: str,
        database: str,
        database_prefix: str = "",
        query_columns: str = "*",
        table: Optional[str] = None,
        order_by: Optional[list] = None,
        where_clauses: Optional[dict[str, Any]] = None,
        group_by: Optional[str] = None,
        sub_query: Optional[str] = None,
    ) -> list[dict]:
        """Retrieve data from a query or table in databricks as a list of dict objects
        Must provide either a table or sub query.
        """

        if (table is None and sub_query is None) or (table and sub_query):
            raise ValueError(
                "Only one of sub_query and table should be provided as source"
            )

        database_name = database_prefix + database
        tbl = f"{catalog}.{database_name}.{table}"
        query = f"SELECT {query_columns} FROM {sub_query or tbl}"
        if where_clauses:
            query += " WHERE " + " AND ".join(
                f"{k} = {v}" for k, v in where_clauses.items()
            )
        if group_by:
            query += f" GROUP BY {group_by}"
        if order_by:
            query += f" ORDER BY {', '.join(order_by)}"
        resp = self.execute_query(query)
        return [r.asDict() for r in resp]

    def get_table_with_query(self, query: str) -> list[dict]:
        """Query a delta table from databricks and return result as a list of dict objects."""
        resp = self.execute_query(query)
        return [r.asDict() for r in resp]

    def clear_table(self, database: str, table: str) -> None:
        query = f"DELETE FROM {database}.{table}"
        self.execute_update(query)

    def drop_database(self, database: str) -> None:
        """Drop database and contents from hive"""
        query = f"DROP DATABASE IF EXISTS {database} CASCADE"
        self.execute_update(query)

    def create_table_from_dataclass(
        self,
        catalog: str,
        database: str,
        table: str,
        data_cls: Any,
        storage_account_name: str,
        database_prefix: str = "",
        schema_overrides: Optional[dict[str, str]] = None,
    ):
        """Create a table by inferring datatypes from a given dataclass"""

        mapping = {
            "DECIMAL": "DECIMAL(16,6)",
            "MAP": "STRING",
            "VOID": "STRING",
            "ARRAY": "ARRAY<STRING>",
        }

        schema = {}
        fields = asdict(data_cls())

        for name, data_type in fields.items():
            _type = st._infer_type(data_type).typeName().upper()
            schema[name] = mapping.get(_type, _type)

        if schema_overrides:
            schema.update(schema_overrides)

        columns = [f"{str(k)} {schema[k]}" for k in schema]

        database_name = database_prefix + database

        query = f"""
        CREATE TABLE IF NOT EXISTS {catalog}.{database_name}.{table} (
        {', '.join(columns)}
        )
         USING delta
         LOCATION 'abfss://temp@{storage_account_name}.dfs.core.windows.net/{database_name}/{table}'

        """
        return self.execute_query(query)


class QueryManagerFactory:
    def __init__(self, configuration: QueryManagerConfig) -> None:
        self.configuration = configuration

    def get_query_manager_instance(self) -> QueryManager:
        return QueryManager(config=self.configuration)

import pyodbc
import re

from pathlib import Path
from typing import Optional, Union, Iterable, List, Dict, Tuple, Iterator, Any
from common.exceptions import FileProcessingError, SQLExecutionError
from config.config import Config


class QueryResults:

    def __init__(self, fieldnames: List[str], rows: Iterator[Tuple[Any, ...]], as_dict: bool = False):
        self.fieldnames = fieldnames
        self.__rows = rows
        self.__as_dict = as_dict

    def __as_dicts(self) -> Iterator[Dict[str, Any]]:
        for row in self.__rows:
            yield dict(zip(self.fieldnames, row))

    def __as_tuples(self):
        yield from self.__rows

    def __iter__(self):
        return self.__as_dicts() if self.__as_dict else self.__as_tuples()


class DatabaseConnection:

    def __init__(self, config: Config):
        self.config = config
        self.__logger = self.config.get_logger()
        self.__connection: Optional[pyodbc.Connection] = None
        self.__cursor: Optional[pyodbc.Cursor] = None

    def __enter__(self) -> 'DatabaseConnection':
        """Establish a database connection when entering the context."""
        self.__logger.info("Establishing database connection.")
        try:
            self.__connection = pyodbc.connect(self.config.dsn, autocommit=False)
            self.__cursor = self.__connection.cursor()
            return self

        except pyodbc.Error as error:
            self.__logger.error(f"Failed to establish database connection: {error}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close the database connection when exiting the context."""

        if self.__connection or self.__cursor:
            try:
                if exc_type:
                    self.__logger.error("An error occurred, rolling back the transaction.")
                    self.__connection.rollback()
                else:
                    self.__logger.info("Committing database transactions.")
                    self.__connection.commit()
            except pyodbc.Error as error:
                self.__logger.error(f"Failed to commit/rollback transaction: {error}")

            finally:
                self.__logger.info("Closing database connection.")
                self.__cursor.close()
                self.__connection.close()

    def __is_recoverable_exception(self, exc_val) -> bool:
        """Check if an exception is recoverable."""
        if isinstance(exc_val, pyodbc.DatabaseError):
            error_message = str(exc_val).lower()
            return "does not exist" in error_message or "invalid object name" in error_message
        return False

    def execute_dml(self, sql_statement: str,
                    parameters: Optional[Union[Iterable, Iterable[Iterable], Dict, List[Dict], Tuple[Dict, ...]]] = (),
                    field_order: Optional[List[str]] = None
                    ) -> None:
        """
        Executes a DML statement.
        Supports single-row and multi-row operations by inspecting parameter structure.
        Can accept dictionaries or list of dictionaries if param_order is provided,
        which defines the keys order to extract values from dict(s).
        """

        def dict_to_iterable(parameters, order):
            if isinstance(parameters, dict):
                return tuple(parameters[key] for key in order)
            return [tuple(param[key] for key in order) for param in parameters]

        self.__check_statement(sql_statement)

        if isinstance(parameters, dict) or (
                isinstance(parameters, (list, tuple)) and parameters and isinstance(parameters[0], dict)):
            if not field_order:
                raise ValueError("field_order must be provided when using dictionary-based parameters.")
            parameters = dict_to_iterable(parameters, field_order)

        is_bulk = isinstance(parameters, (list, tuple)) and parameters and isinstance(parameters[0], (list, tuple))

        try:
            self.__logger.info(f"Executing statement. {sql_statement[:20]}...")

            if is_bulk:
                self.__cursor.executemany(sql_statement, parameters)
            else:
                self.__cursor.execute(sql_statement, parameters)

            self.__logger.info("DML statement executed successfully.")

        except pyodbc.DatabaseError as dberror:
            self.__logger.error(f"Database error occurred: {dberror}", exc_info=True)
            raise

        except Exception as error:
            self.__logger.error(f"An error occurred: {error}", exc_info=True)
            raise

    def execute_query(self,
                      sql_statement: str,
                      parameters: Optional[tuple] = (),
                      batch_size: Optional[int] = 10000,
                      is_dict: Optional[bool] = False,
                      ) -> Union[QueryResults, List[Union[dict, tuple]]]:

        """Executes SQL select statements and returns results"""

        self.__check_statement(sql_statement)
        try:
            self.__logger.info(f"Executing Query. {sql_statement[:50]}...")
            self.__cursor.execute(sql_statement, parameters)
            fieldnames = []
            for column in self.__cursor.description:
                if column[0] in fieldnames:
                    fieldnames.append(f"{column[0]}_1")
                else:
                    fieldnames.append(column[0])

            def row_generator():
                while True:
                    rows = self.__cursor.fetchmany(batch_size)
                    if not rows:
                        self.__logger.info("Either no records exist or all have been processed.")
                        break

                    for row in rows:
                        yield row

            return QueryResults(fieldnames=fieldnames, rows=row_generator(), as_dict=is_dict)

        except pyodbc.DatabaseError as dberror:
            self.__logger.error(f"Database error occurred: {dberror}", exc_info=True)
            raise

        except Exception as error:
            self.__logger.error(f"An error occurred: {error}", exc_info=True)
            raise

    def commit(self):
        if self.__connection:
            self.__connection.commit()
            self.__logger.info("Explicit commit called.")

    def __check_statement(self, sql_statement: str):
        if not sql_statement:
            raise SQLExecutionError("SQL statement is empty.")

    def __parse_statement(self, sql_statement: str) -> str:
        """
        Parses a SQL statement by removing comments, extra spaces, and semicolons.
        """

        try:
            sql_statement = re.sub(r'--.*', '', sql_statement)
            sql_statement = re.sub(r'/\*[\s\S]*?\*/', '', sql_statement)
            sql_statement = re.sub(r';', '', sql_statement)
            sql_statement = "\n".join(line.strip() for line in sql_statement.splitlines())
            sql_statement = re.sub(r'\s+', ' ', sql_statement)

            return sql_statement

        except Exception as error:
            self.__logger.error(f"Error while parsing SQL statement: {error}")
            raise SQLExecutionError("Failed to parse SQL statement") from error

    def read_sql_file(self, sql_file_path: Path) -> Optional[str]:
        """
        Read sql file
        """
        try:
            with open(sql_file_path, 'r') as sql_file:
                self.__logger.info(f"Reading sql statement from file: {sql_file_path}")
                sql_statement = sql_file.read()
                self.__check_statement(sql_statement)

            return sql_statement

        except FileNotFoundError as fnf_error:
            raise FileProcessingError(f"SQL file not found at {sql_file_path}") from fnf_error

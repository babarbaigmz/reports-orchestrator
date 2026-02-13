from typing import Optional
from dataclasses import dataclass, field
from common.constants import ProcessOperations
from common.database_operations import DatabaseConnection
from config.config import Config


@dataclass
class ProcessLog:
    process: str
    config: Config
    connection: DatabaseConnection
    log_table: str = field(default='SCHEMA.PROCESS_LOG', init=False)

    def __post_init__(self):
        # Initialize the logger using the provided config object
        self.logger = self.config.get_logger()  # Use the logger from the external config

    def __get_statement(self, operation) -> Optional[str]:
        """Generates SQL statements based on the operation."""

        sql_statement = {
            ProcessOperations.PROCESS_INSERT.value: f"""
            INSERT INTO {self.log_table} (PROCESS_NAME, PROCESS_START_TIME)
            VALUES (?, CURRENT_TIMESTAMP)
            """,
            ProcessOperations.PROCESS_UPDATE.value: f"""
            UPDATE {self.log_table} 
            SET PROCESS_END_TIME = CURRENT_TIMESTAMP, PROCESS_STATUS = ?, MESSAGE = ?
            WHERE PROCESS_NAME = ?
            AND CAST(PROCESS_START_TIME AS DATE) = CAST (? AS DATE)
            """,
            ProcessOperations.PROCESS_DELETE.value: f"""
            DELETE FROM {self.log_table} 
            WHERE PROCESS_NAME = ?
            AND CAST(PROCESS_START_TIME AS DATE) = CAST (? AS DATE)
            """
        }

        return sql_statement.get(operation.upper()).strip()

    def execute_log(self, operation: str, **kwargs) -> None:
        """
        Executes the given database operation (insert/update) on the log table.

        Args:
            operation (str): The database operation to perform (insert/update).
            kwargs: Optional parameters like status, message, process_date for updates.

        Raises:
            ValueError: If the operation is unsupported.
            Exception: If any error occurs during the database transaction.
        """

        if operation not in (ProcessOperations.PROCESS_INSERT.value, ProcessOperations.PROCESS_UPDATE.value):
            raise ValueError("Unsupported database operation.")

        sql_statement = self.__get_statement(operation)

        if not sql_statement:
            raise ValueError(f"Unsupported database operation.")

        # Extract parameters
        status: Optional[str] = kwargs.get('status')
        message: Optional[str] = kwargs.get('message')
        process_date: Optional[str] = kwargs.get('process_date')

        # Use context manager for handling connection and cursor automatically
        with self.connection as conn:
            if operation.upper() == ProcessOperations.PROCESS_INSERT.value:
                # Only one records is stored in the log table for each day.
                conn.execute_dml(self.__get_statement(ProcessOperations.PROCESS_DELETE.value),
                                 (self.process, process_date))
                conn.execute_dml(sql_statement, (self.process,))
            elif operation.upper() == ProcessOperations.PROCESS_UPDATE.value:
                conn.execute_dml(sql_statement, (status, message, self.process, process_date))
        self.logger.info(f"Process Log {operation.title()} successful for process '{self.process}'")

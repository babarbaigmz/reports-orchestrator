import subprocess

from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

from config.config import Config
from common.send_email import EmailSender
from common.constants import ProcessFormats, LogDetails, ProcessOperations
from common.process_log import ProcessLog
from common.database_operations import DatabaseConnection


class Reports:

    def __init__(self, config: Config, email_sender: EmailSender, process_log: ProcessLog,
                 connection: DatabaseConnection) -> None:
        self.config = config
        self.email_sender = email_sender
        self.process_log = process_log
        self.__connection = connection
        self.logger = self.config.get_logger()
        self.email_sender.add_attachments(self.config.log_file_name)

        # Query to extract processes from process_log table
        self.__query = f"""SELECT PROCESS_ID,PROCESS_NAME,SCRIPT_NAME,SCRIPT_FULL_PATH,PARENT_PROCESS_ID 
                           FROM SCHEMA.PROCESS_CONTROL ORDER BY PROCESS_ID;"""

    def __get_data(self) -> List:
        process_data = []

        # Use context manager for handling connection and cursor automatically
        with self.__connection as conn:
            process_data = [rows for rows in conn.execute_query(self.__query.strip(), is_dict=True)]

        return process_data

    def __load_script_hierarchy(self) -> tuple:
        process_hierarchy = defaultdict(list)
        process_data = self.__get_data()

        for process in process_data:
            process_id = process['PROCESS_ID']
            process_parent_id = process['PARENT_PROCESS_ID']

            if process_parent_id:
                process_hierarchy[process_parent_id].append(process_id)
        return process_data, process_hierarchy

    def __run_process(self, process_path: Path) -> tuple:
        # Function to run a script using subprocess
        try:
            self.logger.info(f"Running {process_path.name}")
            main_path = Path(__file__).resolve().parent.parent / process_path
            process = subprocess.Popen(['python', main_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                return False, stderr.decode()

            return True, stdout.decode()

        except Exception as error:
            self.logger.error(f"Exception occurred while running {process_path.name}: {error}", exc_info=True)
            return False, str(error)

    def __execute_main_processes(self) -> None:
        try:
            start_date = datetime.now().date()
            self.email_sender.log_email(
                body=f"{self.process_log.process} process started at {datetime.now().strftime(ProcessFormats.TIME_FORMAT.value)}.")
            self.process_log.execute_log(ProcessOperations.PROCESS_INSERT.value, process_date=start_date)
            process_data, process_hierarchy = self.__load_script_hierarchy()
            main_processes = [process['PROCESS_ID'] for process in process_data if process['PARENT_PROCESS_ID'] is None]
            status = self.__run_processes_in_parallel(main_processes, process_data, process_hierarchy,
                                                      is_main_process=True)

            if status:
                self.process_log.execute_log(operation=ProcessOperations.PROCESS_UPDATE.value,
                                             status='SUCCESS',
                                             message='No Errors encountered.',
                                             process_date=start_date
                                             )

                self.email_sender.log_email(
                    body=f"{self.process_log.process} process finished successfully at {datetime.now().strftime(ProcessFormats.TIME_FORMAT.value)}.",
                    attachments=self.email_sender.get_attachments()
                    )
            else:
                self.__log_error("Process failed with error. Check log file for details.", start_date)
                self.__notify_failure("One of the processes failed with error. Check log file for details:")

        except Exception as error:
            try:
                self.__log_error(
                    f"Errors encountered during {self.process_log.process} process. Check log file for details. {error}",
                    start_date)
            except Exception as log_error:
                self.logger.error(f"Failed to log process: {log_error}", exc_info=True)
            self.__notify_failure(
                f"Exception occurred during {self.process_log.process} process. Check log file for details.")

    def __run_processes_in_parallel(self, processes: list, process_data: dict, process_hierarchy: dict,
                                    is_main_process: bool = False) -> bool:
        status = True

        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(self.__run_process, Path(process['SCRIPT_FULL_PATH'])): process['PROCESS_ID'] for
                       process in process_data if process['PROCESS_ID'] in processes}

            for future in as_completed(futures):
                process_id = futures[future]
                process_name = next(
                    (process['PROCESS_NAME'] for process in process_data if process['PROCESS_ID'] == process_id), None)

                try:
                    success, output = future.result()
                    if success:
                        self.logger.info(
                            f"{'Main' if is_main_process else 'Child'} process {process_name} completed successfully.")
                        # Recursively run the dependent processes (children)
                        child_processes = process_hierarchy.get(process_id, [])

                        if child_processes:
                            self.__run_processes_in_parallel(child_processes, process_data, process_hierarchy)
                    else:
                        if is_main_process:
                            self.logger.error(
                                f"Error running {process_name} failed to execute, skipping its dependents: {output}")
                        else:
                            self.logger.error(f"Error running {process_name}: {output}")
                        status = False
                except Exception as error:
                    self.logger.error(
                        f"Exception occurred while running {'main' if is_main_process else 'child'} process {process_name}: {error}",
                        exc_info=True)
                    status = False

        return status

    def __log_error(self, message: str, process_date) -> None:
        self.process_log.execute_log(operation=ProcessOperations.PROCESS_UPDATE.value,
                                     status='ERROR',
                                     message=message,
                                     process_date=process_date)

    def __notify_failure(self, message: str) -> None:
        self.email_sender.log_email(body=message,
                                    attachments=self.email_sender.get_attachments(),
                                    log_type=LogDetails.LOG_ERROR.value,
                                    importance=2,
                                    exec_info=True
                                    )

    def run_reports(self) -> None:
        self.__execute_main_processes()

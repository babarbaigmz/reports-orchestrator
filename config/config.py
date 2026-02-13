"""
Config file to load configuration parameters.
"""
import yaml
import logging
import logging.config

from pathlib import Path
from datetime import datetime
from common.constants import ProcessFormats

CONFIG_FILE = 'config.yaml'


class Config:
    """
    Config class to set configuration parameters and logging.
    """

    def __init__(self, filename: str = CONFIG_FILE, log_filename=None):
        # Get the path to the config.yaml file
        self.path = Path(__file__).parent / filename

        # Load configuration parameters and set logging from configuration yaml file
        self.__load_config(log_filename)
        self.__config_logging()

    def __load_config(self, log_filename):

        try:
            with open(self.path, mode='r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)

            # Read file, sql script and email configuration parameters
            self.file_config = self.config['file_config']
            self.email_config = self.config['email_config']
            self.sender = self.email_config['sender']
            self.recipients = self.email_config['recipients']

            # DSN details
            self.dsn = self.config['database']['dsn']

            # Create log directory if it doesn't exist.
            self.log_folder = Path(__file__).parent.parent / self.file_config['log_folder']
            self.log_folder.mkdir(parents=False, exist_ok=True)

            # Get log file name from config file
            self.__logging_config = self.config.get('logging')
            self.log_file_name = self.__get_log_filename(log_filename)
            self.__logging_config['handlers']['filehandler']['filename'] = str(self.log_file_name)

        except Exception as error:
            print("Error parsing YAML file: {error}")
            raise

    def __get_log_filename(self, log_filename=None) -> Path:
        if log_filename:
            log_path = Path(log_filename)

            if log_path.suffix != 'log':
                log_filename = f"{log_path.stem}.log"

            log_filename = self.log_folder / self.rename_file(log_filename)
        else:
            log_filename = self.log_folder / self.rename_file(
                self.__logging_config['handlers']['filehandler']['filename'])

        return log_filename

    def __config_logging(self):
        try:
            # Set logging configuration
            logging.config.dictConfig(self.__logging_config)

        except Exception as error:
            print("Error loading logging configurtion: {error}")
            raise

    @staticmethod
    def rename_file(filename: str) -> str:
        return f"{filename.split('.')[0]}_{datetime.strftime(datetime.now().astimezone(), ProcessFormats.DATE_FORMAT.value)}.{filename.split('.')[-1]}"

    def get_logger(self, logger_name=__name__):
        """Returns a logger with the specified name"""
        return logging.getLogger(logger_name)

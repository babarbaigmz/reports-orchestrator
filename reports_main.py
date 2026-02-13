from reports import Reports
from config.config import Config
from common.send_email import EmailSender
from common.constants import ProcessFormats
from common.process_log import ProcessLog
from common.database_operations import DatabaseConnection
from common.get_edge_driver import GetEdgeDriver


def main():
    config = Config()
    connection = DatabaseConnection(config=config)
    reports = Reports(config=config,
                      email_sender=EmailSender(config=config),
                      process_log=ProcessLog(process='Reports', config=config, connection=connection),
                      connection=connection
                      )

    reports.run_reports()


if __name__ == '__main__':
    main()

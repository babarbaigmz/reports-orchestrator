import win32com.client as win32

from pathlib import Path
from typing import List
from config.config import Config
from common.constants import EmailDetails, LogDetails


class EmailSender:

    def __init__(self, config: Config):
        self.config = config
        self.logger = self.config.get_logger()
        self.__attachments: List = []

    def add_attachments(self, *args: Path, reset=False) -> None:
        if reset:
            self.__attachments.clear()
        for file in args:
            self.__attachments.append(file)

    def get_attachments(self) -> List:
        return self.__attachments

    def __send_email(self,
                     subject: str,
                     body: str,
                     attachments: List = [],
                     importance: int = EmailDetails.EMAIL_NORMAL.value,
                     to_support: bool = False
                     ):

        # Get a COM object for Outlook
        outlook = win32.Dispatch(EmailDetails.EMAIL_SERVER.value)

        # Get the current Windows user's Outlook account
        # namespace = outlook.GetNamespace(EmailDetails.EMAIL_NAMESPACE.value)
        # current_user_email = namespace.CurrentUser.Address

        mail = outlook.CreateItem(0)

        # set mail attributes
        mail.Sender = self.config.sender
        # mail.Sender=current_user_email
        # mail.HtmlBody=

        if to_support:
            if self.config.recipients_support:
                mail.To = self.config.recipients_support
            else:
                self.logger.warning("No support recipients found in the configuration.")

            if self.config.recipients_cc:
                mail.CC = self.config.recipients_cc
            else:
                self.config.recipients_cc = ""
        else:
            mail.To = self.config.recipients

        mail.Subject = subject

        # Create HTML body
        html_body = f"""
        <html>
            <body>
                <p style="font-size: 16px;">{body}</p>
                <br>
                <p style="font-size: 12px; color: gray;">
                </p>
                <br>
            </body>
        </html>
        """
        # Set HTML body with signature
        mail.HTMLBody = html_body

        # mail.Body= body
        mail.Importance = importance

        if isinstance(attachments, list):
            for attachment in attachments:
                if attachment.exists():
                    mail.Attachments.Add(str(attachment))

        mail.Send()

    def log_email(self,
                  subject: str = 'Reports Process: ',
                  body: str = '', attachments: List = [],
                  log_type: str = LogDetails.LOG_INFO.value,
                  importance: int = EmailDetails.EMAIL_NORMAL.value,
                  to_support: bool = False,
                  exec_info: bool = False
                  ):

        if exec_info or log_type == LogDetails.LOG_ERROR.value:
            subject = f"FAILED: {subject}"
            importance = EmailDetails.EMAIL_HIGH.value

        # Map log_type to appropriate logging function, default to 'info'
        log_func = {LogDetails.LOG_DEBUG.value: self.logger.debug,
                    LogDetails.LOG_INFO.value: self.logger.info,
                    LogDetails.LOG_WARNING.value: self.logger.warning,
                    LogDetails.LOG_ERROR.value: self.logger.error,
                    LogDetails.LOG_CRITICAL.value: self.logger.critical
                    }.get(log_type.upper(), self.logger.info)

        # Log the message with or without execution info
        log_func(f"{subject}{body}", exc_info=exec_info)

        # Send the email
        self.__send_email(subject=subject,
                          body=body,
                          attachments=attachments,
                          importance=importance,
                          to_support=to_support
                          )

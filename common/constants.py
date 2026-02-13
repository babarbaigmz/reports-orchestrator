from enum import Enum,unique

@unique
class ProcessFormats(Enum):
    DATE_FORMAT="%Y-%m-%d"
    TIME_FORMAT="%d-%m-%Y %H:%M:%S"

@unique
class EmailDetails(Enum):
    EMAIL_SERVER="outlook.application"
    EMAIL_NAMESPACE="MAPI"
    EMAIL_LOW=0
    EMAIL_NORMAL=1
    EMAIL_HIGH=2

@unique
class LogDetails(Enum):
    LOG_DEBUG='DEBUG'
    LOG_INFO='INFO'
    LOG_WARNING='WARNING'
    LOG_ERROR='ERROR'
    LOG_CRITICAL='CRITICAL'

@unique
class ProcessOperations(Enum):
    PROCESS_INSERT='INSERT'
    PROCESS_UPDATE='UPDATE'
    PROCESS_DELETE='DELETE'

@unique
class FileModes(Enum):
    MODE_WRITE='w'
    MODE_APPEND='a'
    MODE_READ = 'r'

@unique
class EnvVar(Enum):
    USERNAME = 'USERNAME'
    ENVIRONMENT = 'ENVIRONMENT'
    HTTP_PROXY = 'HTTP_PROXY'
    HTTPS_PROXY = 'HTTPS_PROXY'
    PATH = 'PATH'
    HOME = 'HOME'
    SHELL = 'SHELL'


@unique
class FileFormat(Enum):
    FORMAT_CSV = 'csv'
    FORMAT_TXT = 'txt'
    FORMAT_EXCEL = 'xlsx'
    FORMAT_EXCLM = 'xlsm'


class FileFormats:
    FORMAT_TEXTS = (FileFormat.FORMAT_CSV, FileFormat.FORMAT_TXT)
    FORMAT_EXCELS = (FileFormat.FORMAT_EXCEL, FileFormat.FORMAT_EXCLM)

    @classmethod
    def text_extensions(cls) -> set[str]:
        return {f.value for f in cls.FORMAT_TEXTS}

    @classmethod
    def excel_extensions(cls) -> set[str]:
        return {f.value for f in cls.FORMAT_EXCELS}

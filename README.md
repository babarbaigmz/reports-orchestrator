# Reports Orchestrator

A lightweight **Python orchestration framework** to run scheduled/reporting jobs with **dependency-aware parallel execution**, **Teradata logging**, and **Outlook email notifications**.

This repo includes:
- A process runner that reads a process graph from a control table and executes scripts in parallel with parent/child dependencies.  
- Database utilities for Teradata via `pyodbc` with streaming query results.  
- File utilities for CSV/TXT/Excel exports (OpenPyXL).  
- Windows + Microsoft Edge automation helpers (proxy handling, driver management, Selenium wait/login utilities).

## Suggested GitHub repository name

**`reports-orchestrator`**

Alternatives:
- `teradata-reports-runner`
- `reports-process-orchestrator`
- `process-control-runner`

## Key components

- **Orchestrator / runner**: runs top-level processes and then their dependent child processes; uses a control table to build the dependency tree. (see `reports.py`) fileciteturn0file0L1-L199  
- **Entry point**: `reports_main.py` creates config, DB connection, email sender, process log, then executes the run. fileciteturn0file1L1-L24  
- **DB layer**: `DatabaseConnection` supports DML and streaming SELECTs via `QueryResults`. fileciteturn0file4L1-L132  
- **Process logging**: writes a daily log row into `EWP1AFCB.PROCESS_LOG` (insert/update/delete pattern). fileciteturn0file13L1-L78  
- **Email notifications**: sends Outlook emails and attaches the log file. fileciteturn0file15L1-L105  
- **Config + logging**: YAML-driven settings + `logging.config.dictConfig`. fileciteturn0file2L1-L77  
- **File export helpers**: CSV/TXT + Excel writing and reading utilities. fileciteturn0file9L1-L266  
- **Edge/Selenium helpers**: driver lifecycle, waits, login, proxy handling, and Edge driver version management. fileciteturn0file5L1-L118 fileciteturn0file17L1-L39 fileciteturn0file12L1-L60 fileciteturn0file14L1-L35 fileciteturn0file7L1-L127 fileciteturn0file6L1-L23

---

## How it works (high level)

1. **Reads process definitions** from `SCHEMA.PROCESS_CONTROL` (id, name, full script path, parent id). fileciteturn0file0L18-L26  
2. Builds a **dependency graph** (parent → child). fileciteturn0file0L44-L67  
3. Executes **main (no-parent) processes** in parallel via `ThreadPoolExecutor`. fileciteturn0file0L78-L132  
4. After a parent completes, runs its **children** (also parallel) recursively. fileciteturn0file0L120-L161  
5. Writes a **process run log** to `SCHEMA.PROCESS_LOG` and emails results with the log attached. fileciteturn0file0L78-L115 fileciteturn0file15L77-L105  

---

## Prerequisites

### OS / runtime
- **Windows** (required for Outlook COM automation via `win32com`). fileciteturn0file15L1-L10  
- Python 3.10+ recommended

### Dependencies (typical)
- `pyodbc`
- `pyyaml`
- `openpyxl`
- `pywin32`
- `selenium` (only needed if you use the browser automation modules)
- `requests`, `urllib3` (Edge driver downloader)

### Teradata connectivity
- A configured **ODBC DSN** (example in YAML: `"DSN=TD Prod"`). fileciteturn0file2L25-L33  

### Environment variables
- `USERNAME` is used by Edge/driver modules and login automation. fileciteturn0file7L20-L29 fileciteturn0file12L18-L27  
- Optional: `HTTP_PROXY`, `HTTPS_PROXY` (proxy manager clears/restores). fileciteturn0file14L1-L35  

---

## Installation

```bash
git clone <your-repo-url>
cd reports-orchestrator

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
```

> If you don’t have a `requirements.txt` yet, generate one from your environment once dependencies are finalized:
> `pip freeze > requirements.txt`

---

## Configuration

Update `config.yaml` with your environment specifics (log folder, email recipients, DSN, logging handlers). fileciteturn0file2L1-L61  

Example structure (trimmed):

```yaml
file_config:
  log_folder: logs

email_config:
  sender: ""
  recipients: ""

database:
  dsn: "DSN=TD Prod"
```

Logging is configured via `logging.dictConfig` and the file handler path is updated at runtime with a date-stamped filename. fileciteturn0file2L43-L77  

---

## Database tables expected

### `SCHEMA.PROCESS_CONTROL`
Used by the orchestrator to determine what to run and dependency order. fileciteturn0file0L18-L26  

Minimum required columns (as used in code):
- `PROCESS_ID`
- `PROCESS_NAME`
- `SCRIPT_NAME`
- `SCRIPT_FULL_PATH`
- `PARENT_PROCESS_ID`

### `SCHEMA.PROCESS_LOG`
Used by `ProcessLog` to track daily runs. fileciteturn0file13L1-L78  

---

## Running the project

```bash
python reports_main.py
```

The runner will:
- log “started”
- insert a PROCESS_LOG row (after deleting any existing row for the same date/process)
- execute processes in parallel with dependency ordering
- update PROCESS_LOG with SUCCESS/ERROR
- email results and attach the log file fileciteturn0file0L78-L115  

---

## Project structure (suggested)

You can keep your current layout, but this is a clean GitHub-friendly target structure:

```
reports-orchestrator/
  README.md
  config.yaml
  requirements.txt
  reports_main.py
  reports.py
  config/
    __init__.py
    config.py
  common/
    __init__.py
    constants.py
    database_operations.py
    exceptions.py
    file_operations.py
    file_writer.py
    process_log.py
    send_email.py
    subprocess_util.py
    wait_utils.py
    proxy_manager.py
    driver_manager_main.py
    edge_browser_version.py
    edge_driver_version.py
    get_edge_driver.py
    login.py
  logs/
    (generated)
```

---

## Notes / limitations

- Email sending uses Outlook COM (`win32com`) and is Windows/Outlook dependent. fileciteturn0file15L1-L10  
- The Edge driver downloader uses `verify=False` HTTPS requests; ensure your corporate security policies allow this. fileciteturn0file7L33-L88  
- `reports_main.py` currently imports `GetDriver` which is not present in the uploaded files; either remove that import or add the missing module/class. fileciteturn0file1L1-L7  

---

## License

Add your preferred license (e.g., MIT, Apache-2.0, proprietary/internal).


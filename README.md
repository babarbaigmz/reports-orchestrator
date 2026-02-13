# Reports Orchestrator

A lightweight Python orchestration framework for running scheduled reporting jobs with:

- Dependency-aware parallel execution  
- Teradata logging  
- Outlook email notifications  
- Optional Selenium + Microsoft Edge automation support  

---

## Overview

Reports Orchestrator executes reporting or batch scripts based on a database-driven process control table.

It:

1. Reads process definitions from a control table  
2. Builds a parent-child dependency graph  
3. Executes main processes in parallel  
4. Executes dependent child processes recursively  
5. Logs execution status into a database table  
6. Sends Outlook email notifications with log attachments  

Main entry point:

```bash
python reports_main.py
```

---

## Architecture

### Core Components

### Orchestrator
- Builds dependency hierarchy
- Executes processes using ThreadPoolExecutor
- Handles success/failure logic
- Updates process log table

### Database Layer
`DatabaseConnection`
- Context-managed connection handling
- Streaming SELECT results via QueryResults iterator
- DML support (single and bulk execution)
- Automatic commit / rollback

### Process Logging
`ProcessLog`
- INSERT start record
- UPDATE success/error status
- Ensures one record per process per day

### Email Notifications
`EmailSender`
- Uses win32com (Outlook COM automation)
- Sends formatted HTML emails
- Attaches generated log file
- Escalates importance on failure

### Configuration
`config.yaml`
- DSN
- Email recipients
- Logging configuration
- Log folder location

---

## Expected Database Tables

### PROCESS_CONTROL
Required fields:
- PROCESS_ID
- PROCESS_NAME
- SCRIPT_FULL_PATH
- PARENT_PROCESS_ID

### PROCESS_LOG
Tracks:
- PROCESS_NAME
- PROCESS_START_TIME
- PROCESS_END_TIME
- PROCESS_STATUS
- MESSAGE

---

## Project Structure

```
reports-orchestrator/
│
├── reports_main.py
├── reports.py
├── config.yaml
├── README.md
│
├── config/
│   └── config.py
│
├── common/
│   ├── constants.py
│   ├── database_operations.py
│   ├── process_log.py
│   ├── send_email.py
│   ├── file_operations.py
│   ├── file_writer.py
│   ├── proxy_manager.py
│   ├── driver_manager_main.py
│   ├── edge_browser_version.py
│   ├── edge_driver_version.py
│   ├── get_edge_driver.py
│   ├── login.py
│   ├── wait_utils.py
│   ├── subprocess_util.py
│   └── exceptions.py
│
└── logs/
```

---

## Installation

```bash
git clone https://github.com/your-username/reports-orchestrator.git
cd reports-orchestrator

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

Suggested requirements:

```
pyodbc
pyyaml
openpyxl
pywin32
selenium
requests
urllib3
```

---

## Configuration Example

```yaml
file_config:
  log_folder: logs

email_config:
  sender: ""
  recipients: ""

database:
  dsn: "DSN=TD Prod"
```

---

## Running

```bash
python reports_main.py
```

Execution Flow:
- Insert PROCESS_LOG record
- Execute main processes
- Execute dependent child processes
- Update status
- Send success/failure email

---

## Platform Requirements

- Windows (required for Outlook COM automation)
- Python 3.10+
- ODBC DSN configured
- Outlook installed (if using email feature)

---

## Repository Description

Python-based reporting orchestration framework with dependency-aware parallel execution, Teradata logging, and Outlook email notifications. Includes optional Selenium and Microsoft Edge automation utilities.

---

## License

Add your preferred license (MIT, Apache-2.0, or proprietary/internal).

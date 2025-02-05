![image](https://github.com/user-attachments/assets/b8e452f5-239b-4313-975c-0319d54af7e4)

# Database Sync Tool

A web-based tool to synchronize data between MySQL and MariaDB servers. Features automatic daily synchronization at midnight and manual sync capability through a web interface.

## Concept
- The tool is designed to be used as a service to sync the database between the staging and development environment.
- by remmove all the tables on the target database, and re-import the data from the source database
- this will make the migration flow more efficient and easier to investigate the migration flow.

## Features
- Automated daily database synchronization at 00:00
- Manual sync & stop sync trigger through web UI
- Sync status monitoring
- Error logging and notifications

## Tech Stack
- Backend: Python 3.x with FastAPI
- Database Connectors: mysql-connector-python
- Scheduler: APScheduler
- Frontend: HTML, JavaScript, Bootstrap

## Project Structure
```bash
db-sync-tool/
├── readme.md
├── code/
│ ├── .dockerignore
│ ├── Dockerfile
│ ├── docker-compose.yaml
│ ├── requirements.txt
│ ├── main.py
│ ├── config.py
│ ├── static/
│ │ └── index.html
│ │ └── style.css
│ │ └── script.js
│ ├── sync/
│ │ └── db_sync.py
│ ├── config/
│ │ └── config.ini
├── config/
│ └── example.config.ini
├── sync/
│ └── db_sync.py
```

## Setup Instructions
1. Clone the repository
2. create venv for virtual environment
    ```bash
    python -m venv venv
    ```
3. activate venv
    ```bash
    source venv/bin/activate
2. copy config.ini.example to config.ini and configure the database connections
    ```bash
    cp config/config.ini.example code/config/config.ini
    ```
3. go to code folder
    ```bash
    cd code
    ```
4. Install dependencies: `pip install -r requirements.txt`
5. Configure database connections in `code/config/config.ini`
6. Run the application: `uvicorn main:app --reload`

## Docker Setup
1. copy `config/config.ini.example` to `config/config.ini` and configure the database connections
2. Build the Docker image: `docker-compose build`
3. Start the Docker container: `docker-compose up -d`

## Used
1. go to http://localhost:8000/ (http://localhost:5665 on Docker)
2. click the sync button to trigger the sync
3. click the stop button to stop the sync

status will be shown on the page and update every 0.5 second


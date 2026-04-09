# 🏛️ UWI genCAT Improvement Proof-of-Concept

<div align="center">

[![GitHub stars](https://img.shields.io/github/stars/AMMS-INFO3604/Archives-And-Record-Management-UWI-genCAT-Improvement-Proof-of-Concept-?style=for-the-badge)](https://github.com/AMMS-INFO3604/Archives-And-Record-Management-UWI-genCAT-Improvement-Proof-of-Concept-/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/AMMS-INFO3604/Archives-And-Record-Management-UWI-genCAT-Improvement-Proof-of-Concept-?style=for-the-badge)](https://github.com/AMMS-INFO3604/Archives-And-Record-Management-UWI-genCAT-Improvement-Proof-of-Concept-/network)
[![GitHub issues](https://img.shields.io/github/issues/AMMS-INFO3604/Archives-And-Record-Management-UWI-genCAT-Improvement-Proof-of-Concept-?style=for-the-badge)](https://github.com/AMMS-INFO3604/Archives-And-Record-Management-UWI-genCAT-Improvement-Proof-of-Concept-/issues)

**A proof-of-concept for enhancing the University of the West Indies St. Augustine's genCAT Archives and Record Management System using Flask MVC.**

</div>

## 📖 Overview

This repository hosts the code for a proof-of-concept project aimed at improving the existing genCAT system used by the University of the West Indies (UWI), St. Augustine's records department. Developed as part of the INFO 3604 - Project course, this application leverages Flask, Python, and a Model-View-Controller (MVC) architectural pattern to demonstrate a more robust and modern approach to archives and record management. It provides a foundational backend service for handling archival data, user authentication, and core record-keeping functionalities.

## ✨ Features

-   **User Authentication & Authorization**: Secure user management with JSON Web Tokens (JWT) for API access.
-   **Record Management**: Core functionalities for managing archival records and files.
-   **Loan Management**: System for tracking the loaning of physical or digital records.
-   **Database Persistence**: Robust data storage and retrieval using SQLAlchemy with PostgreSQL.
-   **Email Notifications**: Integrated Flask-Mail for sending automated email alerts or notifications.
-   **Modular MVC Design**: Clean separation of concerns with a Flask-based MVC architecture for scalability and maintainability.
-   **Containerized Deployment**: Docker support for consistent development and production environments.

## 🛠️ Tech Stack

**Backend:**
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Gunicorn](https://img.shields.io/badge/Gunicorn-499848?style=for-the-badge&logo=gunicorn&logoColor=white)](https://gunicorn.org/)
[![Flask-JWT-Extended](https://img.shields.io/badge/Flask--JWT--Extended-black?style=for-the-badge)](https://flask-jwt-extended.readthedocs.io/en/stable/)
[![Flask-Mail](https://img.shields.io/badge/Flask--Mail-yellowgreen?style=for-the-badge)](https://pythonhosted.org/Flask-Mail/)

**Database:**
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-336791?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Flask-Migrate](https://img.shields.io/badge/Flask--Migrate-blue?style=for-the-badge)](https://flask-migrate.readthedocs.io/en/latest/)

**Frontend (Server-rendered):**
[![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/CSS)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![Jinja2](https://img.shields.io/badge/Jinja2-purple?style=for-the-badge)](https://jinja.palletsprojects.com/en/3.1.x/)

**DevOps & Tools:**
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com/)
[![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org/)
[![Postman](https://img.shields.io/badge/Postman-FF6C37?style=for-the-badge&logo=postman&logoColor=white)](https://www.postman.com/)
[![VS Code Dev Containers](https://img.shields.io/badge/Dev%20Containers-007ACC?style=for-the-badge&logo=visualstudiocode&logoColor=white)](https://containers.dev/)

## 🚀 Quick Start

Follow these steps to get the development environment up and running.

### Prerequisites

-   [Python 3.9.18](https://www.python.org/downloads/) (specified in `.python-version`)
-   [pip](https://pip.pypa.io/en/stable/installation/) (Python package installer)
-   [Poetry](https://python-poetry.org/docs/#installation) (if using Poetry for package management, although `requirements.txt` suggests `pip`)
-   [PostgreSQL](https://www.postgresql.org/download/) (running locally or accessible)
-   [Docker](https://www.docker.com/get-started) (optional, for containerized development/deployment)

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/AMMS-INFO3604/Archives-And-Record-Management-UWI-genCAT-Improvement-Proof-of-Concept-.git
    cd Archives-And-Record-Management-UWI-genCAT-Improvement-Proof-of-Concept-
    ```

2.  **Set up a Python virtual environment**
    ```bash
    python3.9 -m venv venv
    source venv/bin/activate # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install Python dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Node.js dependencies (for frontend assets, if any)**
    *(Note: While `package.json` is present, it primarily manages JavaScript tooling. If you have any frontend build steps for static assets, you'll need Node.js and npm.)*
    ```bash
    npm install
    ```

5.  **Environment setup**
    Create a `.env` file by copying the example and filling in your details.
    ```bash
    cp .env.example .env
    ```
    Configure your environment variables in `.env`:
    -   `DATABASE_URL`: Your PostgreSQL connection string (e.g., `postgresql://user:password@host:port/database_name`)
    -   `SQLALCHEMY_DATABASE_URI`: Alternative/equivalent for SQLAlchemy.
    -   `SECRET_KEY`: A strong, random secret key for Flask sessions.
    -   `JWT_SECRET_KEY`: A strong, random secret key for Flask-JWT-Extended.
    -   `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD`: SMTP server details for email functionality.
    -   `FLASK_ENV=development`
    -   `DEBUG=True`

6.  **Database setup**
    Initialize and apply database migrations using Flask-Migrate:
    ```bash
    flask db init
    flask db migrate -m "Initial migration" # Or use the existing migration files
    flask db upgrade
    ```

7.  **Start development server**
    ```bash
    flask run
    ```

8.  **Open your browser**
    Visit `http://localhost:5000` (or the port Flask indicates).

## 📁 Project Structure

```
.
├── .Dockerfile                  # Dockerfile for containerization
├── .devcontainer/               # VS Code Dev Container configuration
├── .env.example                 # Example environment variables
├── .flaskenv                    # Flask specific environment configuration
├── .github/                     # GitHub Actions workflows (if any)
├── .gitignore                   # Files ignored by Git
├── .python-version              # Specifies Python version (e.g., 3.9.18)
├── .vscode/                     # VS Code editor settings
├── App/                         # Main Flask application directory (MVC pattern)
│   ├── static/                  # Static assets (CSS, JS, images)
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   ├── templates/               # Jinja2 HTML templates (Views)
│   ├── models/                  # SQLAlchemy database models
│   ├── routes/                  # Flask blueprints/routes (Controllers)
│   └── __init__.py              # Application initialization
├── add_file_tests.py            # Pytest suite for file management features
├── add_loan_tests.py            # Pytest suite for loan management features
├── e2e/                         # End-to-end testing (e.g., Playwright, Selenium)
├── gunicorn_config.py           # Gunicorn production server configuration
├── images/                      # Project-related images/screenshots
├── migrations/                  # Alembic database migration scripts
├── package-lock.json            # npm dependency lock file
├── package.json                 # npm package manifest (for JS tooling/assets)
├── postman_collection.json      # Postman collection for API testing
├── pytest.ini                   # Pytest configuration
├── readme.md                    # Project README file
├── render.yaml                  # Render.com deployment configuration
├── requirements.txt             # Python dependency list
├── setup.cfg                    # Python project configuration
└── wsgi.py                      # WSGI entry point for the Flask application
```

## ⚙️ Configuration

### Environment Variables
The application relies on environment variables for sensitive information and configuration. A `.env.example` file is provided for reference.

| Variable             | Description                                          | Default            | Required |
|----------------------|------------------------------------------------------|--------------------|----------|
| `FLASK_APP`          | The entry point for the Flask application.           | `wsgi.py`          | Yes      |
| `FLASK_ENV`          | Flask environment (`development`, `production`).     | `development`      | Yes      |
| `DEBUG`              | Enable/disable debug mode.                           | `True`             | Yes      |
| `DATABASE_URL`       | PostgreSQL connection string.                        | (None)             | Yes      |
| `SQLALCHEMY_DATABASE_URI` | SQLAlchemy database URI.                       | (None)             | Yes      |
| `SECRET_KEY`         | Flask application secret key.                        | (None)             | Yes      |
| `JWT_SECRET_KEY`     | Secret key for Flask-JWT-Extended.                   | (None)             | Yes      |
| `MAIL_SERVER`        | SMTP server for sending emails.                      | `smtp.gmail.com`   | No       |
| `MAIL_PORT`          | SMTP server port.                                    | `587`              | No       |
| `MAIL_USE_TLS`       | Enable TLS for SMTP connection.                      | `True`             | No       |
| `MAIL_USERNAME`      | Username for SMTP authentication.                    | (None)             | No       |
| `MAIL_PASSWORD`      | Password for SMTP authentication.                    | (None)             | No       |

### Configuration Files
-   `pytest.ini`: Configures Pytest test discovery and options.
-   `gunicorn_config.py`: Customizes Gunicorn server settings for production.
-   `render.yaml`: Defines deployment specifications for Render.com.
-   `setup.cfg`: Basic Python project metadata and build options.

## 🔧 Development

### Available Scripts
The primary development workflow involves Python and Flask commands.

| Command             | Description                                         |
|---------------------|-----------------------------------------------------|
| `flask run`         | Starts the Flask development server.                |
| `flask db init`     | Initializes the Flask-Migrate repository.           |
| `flask db migrate`  | Generates new migration scripts based on model changes. |
| `flask db upgrade`  | Applies pending database migrations.                |
| `pytest`            | Runs all detected Python unit and integration tests. |
| `gunicorn wsgi:app` | Runs the application using Gunicorn (production-ready). |

### Development Workflow
For an optimal development experience, it's recommended to use the provided VS Code Dev Container. This ensures a consistent environment with all prerequisites installed.

1.  Open the project in VS Code.
2.  VS Code will prompt you to "Reopen in Container".
3.  Once the container is built and running, you'll have a fully configured environment.
4.  Run `flask run` in the terminal to start the server.

## 🧪 Testing

This project includes comprehensive testing using Pytest for backend logic and a dedicated `e2e` directory for end-to-end tests. A Postman collection is also provided for API testing.

```bash
# Run all unit and integration tests
pytest

# Run tests for specific modules
pytest add_file_tests.py
pytest add_loan_tests.py
```

-   **End-to-End Tests**: The `e2e/` directory contains tests to simulate user interactions and verify full system flows.
-   **API Testing**: Import `postman_collection.json` into Postman to test the various API endpoints.

## 🚀 Deployment

The application is set up for deployment using Docker and can be easily deployed to platforms like Render.com.

### Production Build (Docker)
A `.Dockerfile` is provided to containerize the application for production.

```bash
# Build the Docker image
docker build -t uwi-gencat-poc .

# Run the Docker container
docker run -p 8000:8000 uwi-gencat-poc
```
The `gunicorn_config.py` specifies how Gunicorn serves the Flask application within the container.

### Deployment Options
-   **Render.com**: A `render.yaml` file is included for seamless deployment to Render.com, defining the service type, build commands, and environment variables.

## 📚 API Reference

This Flask application provides a RESTful API for interacting with the archives and record management system. The full API documentation can be explored using the provided Postman collection.

### Authentication
API endpoints requiring authentication utilize JWT (JSON Web Tokens) for secure access. Users must obtain a token via a login endpoint and include it in the `Authorization` header for subsequent requests.

### Endpoints
The `postman_collection.json` file contains a detailed list of all available API endpoints, their methods, required parameters, and example responses. It covers functionalities such as:

-   User Registration and Login
-   Managing Records (create, retrieve, update, delete)
-   Handling File Uploads and Metadata
-   Managing Loans (request, approve, return)
-   Retrieving System-wide Statistics (e.g., record counts, loan status)

For a complete reference, please import and examine the `postman_collection.json` in your Postman client.

## 🤝 Contributing

We welcome contributions to this proof-of-concept project! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to get started, report bugs, and suggest enhancements.

### Development Setup for Contributors
Ensure you follow the "Quick Start" guide for local setup, and ideally work within the provided VS Code Dev Container for environment consistency.

## 📄 License

This project is licensed under the [LICENSE_NAME](LICENSE) - see the LICENSE file for details. <!-- TODO: Add actual license file (e.g., MIT, Apache 2.0) if not present, and update placeholder. -->

## 🙏 Acknowledgments

-   The University of the West Indies St. Augustine for the genCAT system inspiration.
-   The `uwidcit/flaskmvc` template repository for providing a structured starting point.
-   All contributors to this project.
-   The developers of Flask, SQLAlchemy, Gunicorn, PostgreSQL, and other open-source libraries that make this project possible.

## 📞 Support & Contact

-   🐛 Issues: [GitHub Issues](https://github.com/AMMS-INFO3604/Archives-And-Record-Management-UWI-genCAT-Improvement-Proof-of-Concept-/issues)

---

<div align="center">

**⭐ Star this repo if you find it helpful!**

Made with ❤️ by AMMS-INFO3604

</div>

# Django Commerce

This is a Django-based e-commerce application.

## Prerequisites

- Docker
- Python 3.8+
- pip

## Installation and Setup

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd django_commerce
    ```

2.  **Set up the environment:**

    Create a `.env` file in the root directory and add the following environment variables:

    ```
    SECRET_KEY=<your-secret-key>
    DEBUG=True
    DB_NAME=django_commerce
    DB_USER=user
    DB_PASSWORD=password
    DB_HOST=db
    DB_PORT=5432
    ```

3.  **Build and run the Docker containers:**

    ```bash
    docker-compose up --build
    ```

    This will start the database container and the Django application container. The entrypoint script will handle database migrations and create a superuser.

4.  **Access the application:**

    You can access the application at [http://localhost:8000](http://localhost:8000).

5.  **Access the admin panel:**

    You can access the admin panel at [http://localhost:8000/admin](http://localhost:8000/admin).

    - **Username:** admin
    - **Password:** admin

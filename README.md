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
    - **Password:** admin123

## Database Seeding

The application includes a management command to populate the database with sample data for development and testing purposes.

### Seeding the Database

1. **Prerequisites**
   - Ensure the application is set up and running
   - Install the required Faker package:
     ```bash
     pip install Faker
     ```

2. **Run the seed command**
   ```bash
   python manage.py seed
   ```

### What Gets Created

The seed script will create:

- **Superuser** (if none exists):
  - Username: `admin`
  - Email: `admin@mahimsafa.com`
  - Password: `admin`

- **Categories**:
  - Electronics
  - Clothing
  - Home & Kitchen
  - Books
  - Beauty & Personal Care

- **Stores**:
  1. **Tech Haven** - Electronics store with 12 tech products
  2. **Fashion Forward** - Clothing store with 12 fashion products

Each product includes:
- Default variant with pricing
- Unique SKU
- Detailed description
- Published status

### Notes

- The command is idempotent and can be run multiple times without creating duplicate data.
- Existing data with matching unique constraints (like usernames or slugs) will be skipped.
- All products are assigned to the superuser account.

### Accessing Seeded Data

- **Admin Panel**: Log in at `/admin` with the superuser credentials
- **Stores**:
  - Tech Haven: `/store/tech-haven/`
  - Fashion Forward: `/store/fashion-forward/`
    - **Password:** admin

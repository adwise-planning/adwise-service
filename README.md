# OTP User Registration and Login (Python Flask)

This is a Python Flask-based implementation of user registration and login using One-Time Passwords (OTPs).

## Project Structure

[Describe the project structure as outlined earlier]

## Setup

1.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate  # On Windows
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure environment variables:**
    -   Copy `.env.example` to `.env` and fill in the necessary values (e.g., `SECRET_KEY`, `JWT_SECRET_KEY`).

## Running the Application

```bash
python app/main.py


## Database Setup (PostgreSQL)

1.  **Install PostgreSQL:** If you don't have PostgreSQL installed, follow the instructions for your operating system.
2.  **Create a database:** Create a PostgreSQL database for your application. You can use `psql` or a GUI tool like pgAdmin.
    ```sql
    CREATE DATABASE otp_user_db;
    ```
3.  **Configure database credentials:**  Update the `DATABASE_URL` environment variable in your `.env` file with the correct connection string for your PostgreSQL database (username, password, host, port, database name).

## Running the Application

Before running, ensure your PostgreSQL server is running and the database is created.

```bash
python app/main.py


**9. Update `.env.example` (already done in step 2).**

**To Run the Application with PostgreSQL:**

1.  **Ensure PostgreSQL is running.**
2.  **Create the database** as mentioned in `README.md`.
3.  **Configure `.env`** with your PostgreSQL connection details.
4.  **Run:** `python app/main.py`

When you run `app/main.py` for the first time (or if the database is empty), SQLAlchemy will create the `users` table in your PostgreSQL database.

Now, your user registration and login endpoints are backed by a PostgreSQL database using SQLAlchemy, making the application more robust and suitable for production use. Remember to handle database migrations properly as your application evolves. You can use Flask-Migrate or Alembic for managing database schema changes in a controlled way.
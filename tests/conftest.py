import pytest
import os
import tempfile
from app import app as flask_app, init_db, get_db, DATABASE

@pytest.fixture
def app():
    # Create a temporary database for testing
    db_fd, db_path = tempfile.mkstemp()

    flask_app.config.update({
        "TESTING": True,
        "DATABASE": db_path,
        "SECRET_KEY": "test_secret_key", # Fixed secret key for testing
            "WTF_CSRF_ENABLED": False, # Disable CSRF for simpler form testing
            "SERVER_NAME": "localhost.test" # Added for url_for outside request context
    })

    # Initialize the temporary database with the schema
    with flask_app.app_context():
        # Check if schema.sql needs to be created temporarily for init_db
        if not os.path.exists('schema.sql'):
            with open('schema.sql', 'w') as f:
                f.write('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);
                ''')
            init_db() # This uses flask_app.open_resource which needs app_context
            os.remove('schema.sql') # Clean up schema.sql
        else: # If schema.sql somehow exists, still run init_db
            init_db()


    yield flask_app

    # Clean up: close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

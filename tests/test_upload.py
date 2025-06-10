import pytest
import os
from io import BytesIO
from app import app as flask_app # To access app.config['UPLOAD_FOLDER']

# Helper to log in a user and return the client
def login_test_user(client):
    client.post("/register", data={
        "username": "uploaduser",
        "email": "upload@example.com",
        "password": "password123"
    })
    client.post("/login", data={
        "username": "uploaduser",
        "password": "password123"
    }) # Don't follow redirects, just set session
    return client

# Need url_for for redirect check
from flask import url_for

def test_upload_get_requires_login(client, app): # Added app
    response_get_upload = client.get("/upload") # No follow_redirects
    assert response_get_upload.status_code == 302 # Expect redirect
    with app.app_context(): # For url_for
        assert response_get_upload.headers['Location'] == url_for('login', _external=False)

    # Check session for flash message
    with client.session_transaction() as sess:
        flashes = [(msg, cat) for cat, msg in sess.get('_flashes', [])]
        assert ("Please log in to access this page.", "warning") in flashes

    # Follow redirect and check page content (message may not be in data)
    response_get_login = client.get(response_get_upload.headers['Location'])
    assert response_get_login.status_code == 200
    assert b"Login" in response_get_login.data
    # assert b"Please log in to access this page." in response_get_login.data # This may fail

def test_upload_get_authenticated(client):
    login_test_user(client)
    response = client.get("/upload")
    assert response.status_code == 200
    assert b"Upload Excel File" in response.data
    assert b"Welcome, uploaduser!" in response.data

def test_upload_post_success(client, app):
    login_test_user(client)

    # Ensure UPLOAD_FOLDER exists for the test context
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    data = {
        'file': (BytesIO(b"this is a test xlsx file content"), 'test.xlsx')
    }
    response = client.post("/upload", data=data, content_type='multipart/form-data', follow_redirects=True)

    assert response.status_code == 200
    assert b"File &#39;test.xlsx&#39; uploaded successfully!" in response.data

    # Check if file exists in upload folder
    uploaded_file_path = os.path.join(upload_folder, 'test.xlsx')
    assert os.path.exists(uploaded_file_path)

    # Clean up the created file
    os.remove(uploaded_file_path)

def test_upload_post_no_file_part(client):
    login_test_user(client)
    response = client.post("/upload", data={}, content_type='multipart/form-data', follow_redirects=True)
    assert response.status_code == 200
    assert b"No file part in the request." in response.data

def test_upload_post_no_selected_file(client):
    login_test_user(client)
    data = {
        'file': (BytesIO(b""), '') # Empty filename
    }
    response = client.post("/upload", data=data, content_type='multipart/form-data', follow_redirects=True)
    assert response.status_code == 200
    assert b"No selected file." in response.data

def test_upload_post_invalid_file_type(client, app):
    login_test_user(client)
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder): # Ensure folder exists
        os.makedirs(upload_folder)

    data = {
        'file': (BytesIO(b"this is a text file"), 'test.txt')
    }
    response = client.post("/upload", data=data, content_type='multipart/form-data', follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid file type. Please upload .xls or .xlsx files." in response.data

    # Check that file was not created
    assert not os.path.exists(os.path.join(upload_folder, 'test.txt'))

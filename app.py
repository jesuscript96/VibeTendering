import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, g, current_app # Added current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename # Import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24) # Generates a random secret key
app.config['UPLOAD_FOLDER'] = 'uploads'
DATABASE = 'users.db'
app.config['DATABASE'] = DATABASE

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Helper to check allowed extensions (optional but good practice)
ALLOWED_EXTENSIONS = {'xls', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(current_app.config['DATABASE'])
        db.row_factory = sqlite3.Row # Allows accessing columns by name
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# Check if the database exists, if not, initialize it
if not os.path.exists(DATABASE):
    # Create schema.sql file
    with open('schema.sql', 'w') as f:
        f.write('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);
        ''')
    # Import g for app_context
    from flask import g
    init_db()
    os.remove('schema.sql') # Clean up schema.sql after use

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('upload_file'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone() is not None:
            error = f"User {username} is already registered."
        elif db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone() is not None:
            error = f"Email {email} is already registered."

        if error is None:
            db.execute(
                'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                (username, email, generate_password_hash(password))
            )
            db.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))

        flash(error, 'error')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('upload_file'))

        flash(error, 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part in the request.', 'error')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file.', 'error')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Save file to a user-specific directory if desired, or just the general uploads folder
            # For simplicity, saving to general uploads folder here
            # user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(session['user_id']))
            # if not os.path.exists(user_folder):
            #     os.makedirs(user_folder)
            # file.save(os.path.join(user_folder, filename))

            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash(f"File '{filename}' uploaded successfully!", 'success')
            return redirect(url_for('upload_file')) # Or redirect to a page showing uploaded files
        elif file and not allowed_file(file.filename):
            flash('Invalid file type. Please upload .xls or .xlsx files.', 'error')
            return redirect(request.url)
        else:
            flash('An unknown error occurred.', 'error')
            return redirect(request.url)

    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

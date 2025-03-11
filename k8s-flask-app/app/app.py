from flask import Flask, request, jsonify, render_template_string
import os
import psycopg2
from datetime import datetime
import traceback
import sys

app = Flask(__name__)


app.config['DEBUG'] = True

# Database connection parameters
DB_HOST = os.environ.get('DB_HOST', 'postgres')
DB_NAME = os.environ.get('DB_NAME', 'postgres')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')

def get_db_connection():
    """Establish and return database connection"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}", file=sys.stderr)
        return None

def init_db():
    """Initialize database tables if they don't exist"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            cursor.close()
            conn.close()
            print("Database initialized successfully", file=sys.stderr)
            return True
        except Exception as e:
            print(f"Database initialization error: {e}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            return False
    print("Failed to get database connection during initialization", file=sys.stderr)
    return False


HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Flask + PostgreSQL on Kubernetes</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        h1 { color: #333; }
        form { margin-bottom: 20px; }
        input[type=text] { width: 300px; padding: 8px; }
        button { padding: 8px 15px; background: #4CAF50; color: white; border: none; cursor: pointer; }
        .message { border-bottom: 1px solid #eee; padding: 10px 0; }
        .timestamp { color: #999; font-size: 0.8em; }
        .status { margin-top: 20px; padding: 10px; border-radius: 5px; }
        .connected { background-color: #dff0d8; color: #3c763d; }
        .disconnected { background-color: #f2dede; color: #a94442; }
        pre.error { background-color: #f8d7da; padding: 10px; color: #721c24; white-space: pre-wrap; }
    </style>
</head>
<body>
    <h1>Flask + PostgreSQL on Kubernetes</h1>
    
    <h2>Add a new message</h2>
    <form action="/add" method="post">
        <input type="text" name="message" placeholder="Type your message here" required>
        <button type="submit">Save</button>
    </form>
    
    <h2>Messages</h2>
    <div id="messages">
        {% if messages %}
            {% for message in messages %}
                <div class="message">
                    <p>{{ message[1] }}</p>
                    <span class="timestamp">{{ message[2] }}</span>
                </div>
            {% endfor %}
        {% else %}
            <p>No messages yet.</p>
        {% endif %}
    </div>
    
    <div class="status {% if db_connected %}connected{% else %}disconnected{% endif %}">
        Database connection: {% if db_connected %}Connected{% else %}Disconnected{% endif %}
    </div>
    
    {% if error %}
        <h3>Error Information:</h3>
        <pre class="error">{{ error }}</pre>
    {% endif %}
</body>
</html>
'''

@app.route('/')
def index():
    """Main page - display messages and status"""
    conn = get_db_connection()
    messages = []
    db_connected = False
    error = None
    
    try:
        if conn:
            db_connected = True
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM messages ORDER BY created_at DESC')
            messages = cursor.fetchall()
            cursor.close()
            conn.close()
        else:
            error = f"Failed to connect to database: host={DB_HOST}, db={DB_NAME}, user={DB_USER}"
    except Exception as e:
        error = f"Error: {str(e)}\n{traceback.format_exc()}"
        print(error, file=sys.stderr)
    
    return render_template_string(HTML_TEMPLATE, 
                                messages=messages, 
                                db_connected=db_connected,
                                error=error)

@app.route('/add', methods=['POST'])
def add_message():
    """Add a new message to the database"""
    message = request.form.get('message', '')
    error = None
    
    try:
        if message:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO messages (message) VALUES (%s)', (message,))
                conn.commit()
                cursor.close()
                conn.close()
            else:
                error = "Could not connect to database"
    except Exception as e:
        error = f"Error adding message: {str(e)}"
        print(error, file=sys.stderr)
        return jsonify({'success': False, 'error': error})
    
    if error:
        return jsonify({'success': False, 'error': error})
    return jsonify({'success': True, 'redirect': '/'})

@app.route('/health')
def health():
    """Health check endpoint"""
    conn = get_db_connection()
    if conn:
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected'})
    return jsonify({'status': 'healthy', 'database': 'disconnected'}), 500

@app.route('/debug')
def debug_info():
    """Debug endpoint to check environment variables and connection info"""
    env_vars = {
        'DB_HOST': DB_HOST,
        'DB_NAME': DB_NAME,
        'DB_USER': DB_USER,

    }
    
    conn_result = "Unknown"
    try:
        conn = get_db_connection()
        if conn:
            conn_result = "Connected"
            conn.close()
        else:
            conn_result = "Failed to connect"
    except Exception as e:
        conn_result = f"Error: {str(e)}"
    
    return jsonify({
        'env': env_vars,
        'database_connection': conn_result,
        'python_version': sys.version,
        'flask_debug': app.debug
    })

if __name__ == '__main__':
    print("Starting Flask application...", file=sys.stderr)
    try:
        init_result = init_db()
        print(f"Database initialization result: {init_result}", file=sys.stderr)
    except Exception as e:
        print(f"Exception during database initialization: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
    
    app.run(host='0.0.0.0', port=5000)

from flask import Flask, request, jsonify, render_template_string
import os
import psycopg2
from datetime import datetime
import traceback
import sys
import socket

app = Flask(__name__)

# Enable Flask debug mode
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

# Improved HTML template with better styling and functionality
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kubernetes Flask PostgreSQL Demo</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css">
    <style>
        body {
            padding-top: 20px;
            background-color: #f8f9fa;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .container {
            max-width: 800px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 0 15px rgba(0,0,0,0.1);
            padding: 30px;
            margin-bottom: 30px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 1px solid #eee;
            padding-bottom: 20px;
        }
        .header h1 {
            color: #343a40;
            font-weight: 600;
        }
        .header p {
            color: #6c757d;
        }
        .message {
            background-color: #f8f9fa;
            border-left: 4px solid #28a745;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 4px;
            transition: transform 0.2s ease;
        }
        .message:hover {
            transform: translateX(5px);
        }
        .message p {
            margin: 0;
            color: #343a40;
        }
        .timestamp {
            color: #6c757d;
            font-size: 0.8em;
            margin-top: 8px;
        }
        .form-container {
            background-color: #e9ecef;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }
        .status-container {
            text-align: center;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
            font-weight: 500;
        }
        .connected {
            background-color: #d4edda;
            color: #155724;
        }
        .disconnected {
            background-color: #f8d7da;
            color: #721c24;
        }
        .card-header {
            background-color: #343a40;
            color: white;
        }
        .info-box {
            background-color: #e2f0fb;
            border-left: 4px solid #0d6efd;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }
        .info-item {
            display: flex;
            margin-bottom: 8px;
        }
        .info-label {
            font-weight: 500;
            width: 140px;
        }
        pre.error {
            background-color: #f8d7da;
            padding: 15px;
            color: #721c24;
            border-radius: 4px;
            white-space: pre-wrap;
            margin-top: 20px;
        }
        .btn-primary {
            background-color: #28a745;
            border-color: #28a745;
        }
        .btn-primary:hover {
            background-color: #218838;
            border-color: #1e7e34;
        }
        #refresh-btn {
            margin-bottom: 20px;
        }
        .pod-info {
            text-align: center;
            margin-top: 15px;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 5px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Flask + PostgreSQL on Kubernetes</h1>
            <p>A demonstration of container orchestration with Kubernetes</p>
            <div class="pod-info">
                Running on pod: <strong>{{ hostname }}</strong>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-12">
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="mb-0">System Information</h5>
                    </div>
                    <div class="card-body">
                        <div class="info-box">
                            <div class="info-item">
                                <span class="info-label">Database Host:</span>
                                <span>{{ db_host }}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Database Name:</span>
                                <span>{{ db_name }}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Connection Status:</span>
                                <span class="badge {{ 'bg-success' if db_connected else 'bg-danger' }}">
                                    {{ 'Connected' if db_connected else 'Disconnected' }}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mb-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">Add a New Message</h5>
                    </div>
                    <div class="card-body form-container">
                        <form action="/add" method="post" id="message-form" class="mb-0">
                            <div class="input-group">
                                <input type="text" class="form-control" name="message" 
                                       placeholder="Type your message here" required>
                                <button class="btn btn-primary" type="submit">Save Message</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>

        <button id="refresh-btn" class="btn btn-outline-secondary">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-arrow-clockwise" viewBox="0 0 16 16">
                <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/>
                <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"/>
            </svg>
            Refresh Messages
        </button>
        
        <div id="messages-container">
            <h4>Messages</h4>
            <div id="messages">
                {% if messages %}
                    {% for message in messages %}
                        <div class="message">
                            <p>{{ message[1] }}</p>
                            <div class="timestamp">{{ message[2] }}</div>
                        </div>
                    {% endfor %}
                {% else %}
                    <div class="alert alert-info">No messages yet. Be the first to add one!</div>
                {% endif %}
            </div>
        </div>
        
        {% if error %}
            <h4 class="mt-4">Error Information</h4>
            <pre class="error">{{ error }}</pre>
        {% endif %}
    </div>

    <script>
        // Add JavaScript for form submission without page reload
        document.getElementById('message-form').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const messageInput = this.elements.message;
            
            fetch('/add', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Clear input field
                    messageInput.value = '';
                    // Refresh messages
                    fetchMessages();
                } else {
                    alert('Error: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while saving the message.');
            });
        });
        
        // Add refresh functionality
        document.getElementById('refresh-btn').addEventListener('click', function() {
            fetchMessages();
        });
        
        function fetchMessages() {
            fetch('/messages')
            .then(response => response.json())
            .then(data => {
                const messagesContainer = document.getElementById('messages');
                
                if (data.messages.length === 0) {
                    messagesContainer.innerHTML = '<div class="alert alert-info">No messages yet. Be the first to add one!</div>';
                    return;
                }
                
                let html = '';
                data.messages.forEach(msg => {
                    html += `
                        <div class="message">
                            <p>${msg.text}</p>
                            <div class="timestamp">${msg.timestamp}</div>
                        </div>
                    `;
                });
                
                messagesContainer.innerHTML = html;
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main page - display messages and status"""
    conn = get_db_connection()
    messages = []
    db_connected = False
    error = None
    hostname = socket.gethostname()

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

    return render_template_string(
        HTML_TEMPLATE,
        messages=messages,
        db_connected=db_connected,
        error=error,
        hostname=hostname,
        db_host=DB_HOST,
        db_name=DB_NAME,
    )

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
                return jsonify({"success": False, "error": error})
    except Exception as e:
        error = f"Error adding message: {str(e)}"
        print(error, file=sys.stderr)
        return jsonify({'success': False, 'error': error})

    return jsonify({"success": True})


@app.route("/messages")
def get_messages():
    """API endpoint to get messages"""
    conn = get_db_connection()
    messages = []

    try:
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM messages ORDER BY created_at DESC")
            db_messages = cursor.fetchall()
            cursor.close()
            conn.close()

            messages = [
                {
                    "id": msg[0],
                    "text": msg[1],
                    "timestamp": msg[2].strftime("%Y-%m-%d %H:%M:%S"),
                }
                for msg in db_messages
            ]
    except Exception as e:
        print(f"Error retrieving messages: {e}", file=sys.stderr)
        return jsonify({"success": False, "error": str(e)})

    return jsonify({"success": True, "messages": messages})


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
        "DB_HOST": DB_HOST,
        "DB_NAME": DB_NAME,
        "DB_USER": DB_USER,
        # Don't include password in debug output
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

    return jsonify(
        {
            "env": env_vars,
            "database_connection": conn_result,
            "python_version": sys.version,
            "flask_debug": app.debug,
            "hostname": socket.gethostname(),
        }
    )

if __name__ == '__main__':
    print("Starting Flask application...", file=sys.stderr)
    try:
        init_result = init_db()
        print(f"Database initialization result: {init_result}", file=sys.stderr)
    except Exception as e:
        print(f"Exception during database initialization: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
    
    app.run(host='0.0.0.0', port=5000)

import os
from flask import Flask, render_template, jsonify, send_from_directory
from flask_cors import CORS
from auth import google_auth
from api_routes import api_bp
from models import init_sample_data

app = Flask(__name__, static_folder='static', template_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'asaknsdjasbjcsanckjsdck')

# Enable CORS for all routes
CORS(app, supports_credentials=True)

# Register blueprints
app.register_blueprint(google_auth)
app.register_blueprint(api_bp, url_prefix='/api')

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    # Initialize sample data
    print("Initializing sample data...")
    init_sample_data()
    
    print("""
    ================================================
    Clarity AI Dispute Resolution System Started
    - Sample tickets loaded
    - Ready to process disputes
    ================================================
    """)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
from flask import Flask, render_template
from flask_cors import CORS
from pathlib import Path
import os
import json
import numpy as np

from config import Config
from blueprints.api import api_bp
from blueprints.api_images import api_images_bp
from blueprints.views import views_bp

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle numpy types"""
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            if np.isnan(obj) or np.isinf(obj):
                return None
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Set custom JSON encoder
    app.json_encoder = NumpyEncoder
    
    # Enable CORS for API endpoints
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Create cache directory if it doesn't exist
    os.makedirs(app.config['CACHE_DIR'], exist_ok=True)
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(api_images_bp, url_prefix='/api')
    app.register_blueprint(views_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.html', error='Page not found'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.html', error='Internal server error'), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
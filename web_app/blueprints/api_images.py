"""
Additional API endpoints for serving local images
"""
from flask import Blueprint, jsonify, send_file, current_app
from pathlib import Path

api_images_bp = Blueprint('api_images', __name__)

@api_images_bp.route('/local-image/<path:image_path>')
def serve_local_image(image_path):
    """Serve local images from the data directory"""
    try:
        # Construct the full path
        full_path = current_app.config['BASE_DIR'] / 'data' / 'raw' / image_path
        
        # Security check - ensure the path doesn't go outside our image directory
        if '..' in image_path or image_path.startswith('/'):
            return jsonify({'error': 'Invalid path'}), 400
        
        if full_path.exists() and full_path.is_file():
            # Determine mimetype
            mimetype = 'image/jpeg'
            if full_path.suffix.lower() in ['.png']:
                mimetype = 'image/png'
            elif full_path.suffix.lower() in ['.gif']:
                mimetype = 'image/gif'
            elif full_path.suffix.lower() in ['.svg']:
                mimetype = 'image/svg+xml'
            
            return send_file(full_path, mimetype=mimetype)
        else:
            return jsonify({'error': 'Image not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
from flask import Blueprint, render_template

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def index():
    """Main dashboard view"""
    return render_template('index.html')

@views_bp.route('/anomalies')
def anomalies():
    """Anomalies analysis view"""
    return render_template('anomalies.html')

@views_bp.route('/clustering')
def clustering():
    """Clustering analysis view"""
    return render_template('clustering.html')

@views_bp.route('/search')
def search():
    """Advanced search view"""
    return render_template('search.html')
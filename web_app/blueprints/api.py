from flask import Blueprint, jsonify, request, current_app, send_file
import pandas as pd
import json
from pathlib import Path

from services.data_service import DataService
from services.horizons_service import HorizonsService
from services.images_service import ImagesService
from utils.cache import cached_response
from utils.json_utils import dataframe_to_json_safe, series_to_json_safe

api_bp = Blueprint('api', __name__)

# Initialize services
data_service = DataService()
horizons_service = HorizonsService()
images_service = ImagesService()

@api_bp.route('/objects', methods=['GET'])
def get_objects():
    """Get list of solar system objects with optional filtering"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', current_app.config['DEFAULT_PAGE_SIZE']))
        page_size = min(page_size, current_app.config['MAX_PAGE_SIZE'])
        
        # Filters
        ui_category = request.args.get('category')
        has_anomaly = request.args.get('anomaly', '').lower() == 'true'
        min_radius = request.args.get('min_radius', type=float)
        max_radius = request.args.get('max_radius', type=float)
        search = request.args.get('search')
        
        # Get filtered data
        objects = data_service.get_objects(
            category=ui_category,
            has_anomaly=has_anomaly,
            min_radius=min_radius,
            max_radius=max_radius,
            search=search
        )
        
        # Pagination
        total = len(objects)
        start = (page - 1) * page_size
        end = start + page_size
        objects_page = objects[start:end]
        
        # Convert to dict for JSON response using safe conversion
        objects_dict = dataframe_to_json_safe(objects_page)
        
        return jsonify({
            'success': True,
            'data': objects_dict,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': (total + page_size - 1) // page_size
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/objects/<object_id>', methods=['GET'])
@cached_response(timeout=3600)
def get_object_detail(object_id):
    """Get detailed information for a specific object including orbital data and images"""
    try:
        # Get basic object data
        obj = data_service.get_object_by_id(object_id)
        if obj is None:
            return jsonify({
                'success': False,
                'error': 'Object not found'
            }), 404
        
        # Convert to dict using safe conversion
        if hasattr(obj, 'to_dict'):
            obj_dict = series_to_json_safe(obj)
        else:
            obj_dict = dict(obj)
        
        # Ensure all required fields exist
        obj_dict['id'] = obj_dict.get('id', object_id)
        obj_dict['display_name'] = obj_dict.get('display_name') or obj_dict.get('name', 'Unknown')
        
        # Calculate radius if only diameter is available
        if 'mean_radius_km' not in obj_dict and 'diameter_km' in obj_dict:
            obj_dict['mean_radius_km'] = obj_dict['diameter_km'] / 2.0
        
        # Try to get orbital data from Horizons
        orbital_data = None
        if obj_dict.get('has_orbital_data', True):  # Default to True to attempt fetch
            try:
                orbital_data = horizons_service.get_orbital_data(object_id, obj_dict.get('name'))
                # Merge Horizons data with existing data if available
                if orbital_data and orbital_data.get('source') == 'horizons':
                    # Update with fresh data from Horizons
                    for key in ['absolute_magnitude', 'diameter_km', 'rotation_period_hours']:
                        if key in orbital_data and orbital_data[key] is not None:
                            obj_dict[f'horizons_{key}'] = orbital_data[key]
            except Exception as e:
                print(f"Error fetching Horizons data: {e}")
        
        # Try to get image
        image_data = None
        try:
            # Parse alternative names if it's a string
            alt_names = obj_dict.get('alternative_names', [])
            if isinstance(alt_names, str):
                try:
                    import json
                    alt_names = json.loads(alt_names) if alt_names else []
                except:
                    # Try to split by comma if not valid JSON
                    alt_names = [n.strip() for n in alt_names.split(',') if n.strip()]
            
            image_data = images_service.fetch_image(
                obj_dict.get('name'),
                obj_dict.get('ui_category') or obj_dict.get('object_type'),
                alt_names,
                object_id=object_id
            )
        except Exception as e:
            print(f"Error fetching image: {e}")
        
        # Add discovery information
        discovery_info = {}
        if obj_dict.get('discovered_by'):
            discovery_info['discoverer'] = obj_dict['discovered_by']
        if obj_dict.get('discovery_date'):
            discovery_info['date'] = obj_dict['discovery_date']
        
        # Add classification info
        classification = {
            'primary_type': obj_dict.get('ui_category', obj_dict.get('object_type', 'Unknown')),
            'is_neo': obj_dict.get('is_neo', False),
            'is_pha': obj_dict.get('is_pha', False),
            'is_anomaly': obj_dict.get('is_anomaly', False)
        }
        if obj_dict.get('anomaly_type'):
            classification['anomaly_type'] = obj_dict['anomaly_type']
        
        # Combine all data
        response_data = {
            'success': True,
            'data': {
                **obj_dict,
                'orbital_data': orbital_data,
                'image': image_data,
                'discovery': discovery_info if discovery_info else None,
                'classification': classification
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/stats', methods=['GET'])
@cached_response(timeout=3600)
def get_stats():
    """Get dashboard statistics"""
    try:
        stats_path = current_app.config['DATA_DIR'] / 'dashboard_stats.json'
        with open(stats_path, 'r') as f:
            stats = json.load(f)
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/anomalies', methods=['GET'])
def get_anomalies():
    """Get list of anomalous objects with explanations"""
    try:
        anomalies = data_service.get_anomalies()
        
        # Add explanations for each anomaly type
        anomaly_explanations = {
            'DBSCAN_Outlier': 'Object with unusual orbital or physical characteristics that doesn\'t fit into normal clusters',
            'High_Eccentricity': 'Object with highly elliptical orbit (eccentricity > 0.5)',
            'High_Inclination': 'Object with orbit significantly tilted from the solar system plane (> 30°)',
            'Large_Size': 'Exceptionally large object for its category',
            'Fast_Rotation': 'Object rotating much faster than typical for its size',
            'Unusual_Composition': 'Object with atypical density or albedo values'
        }
        
        # Enrich anomalies with explanations
        anomalies_enriched = anomalies.copy()
        anomalies_enriched['anomaly_explanation'] = anomalies_enriched['anomaly_type'].map(
            lambda x: anomaly_explanations.get(x, 'Unusual characteristics detected')
        )
        
        # Add specific reasons based on data
        for idx, row in anomalies_enriched.iterrows():
            reasons = []
            
            # Check eccentricity
            if pd.notna(row.get('eccentricity')) and row['eccentricity'] > 0.5:
                reasons.append(f"High eccentricity: {row['eccentricity']:.3f}")
            
            # Check inclination
            if pd.notna(row.get('inclination_deg')) and row['inclination_deg'] > 30:
                reasons.append(f"High inclination: {row['inclination_deg']:.1f}°")
            
            # Check size
            if pd.notna(row.get('mean_radius_km')) and row['mean_radius_km'] > 500:
                reasons.append(f"Large size: {row['mean_radius_km']:.0f} km radius")
            elif pd.notna(row.get('diameter_km')) and row['diameter_km'] > 1000:
                reasons.append(f"Large size: {row['diameter_km']:.0f} km diameter")
            
            # Check rotation
            if pd.notna(row.get('rotation_period_h')) and row['rotation_period_h'] < 3:
                reasons.append(f"Fast rotation: {row['rotation_period_h']:.2f} hours")
            
            anomalies_enriched.at[idx, 'specific_reasons'] = reasons
        
        # Group by anomaly type for statistics
        anomaly_stats = anomalies_enriched.groupby('anomaly_type').size().to_dict()
        
        # Pagination
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        anomaly_type_filter = request.args.get('anomaly_type')
        
        # Filter by anomaly type if requested
        if anomaly_type_filter:
            anomalies_enriched = anomalies_enriched[
                anomalies_enriched['anomaly_type'] == anomaly_type_filter
            ]
        
        total = len(anomalies_enriched)
        start = (page - 1) * page_size
        end = start + page_size
        anomalies_page = anomalies_enriched[start:end]
        
        # Convert specific_reasons to list in the JSON output
        anomalies_dict = dataframe_to_json_safe(anomalies_page)
        
        return jsonify({
            'success': True,
            'data': anomalies_dict,
            'statistics': anomaly_stats,
            'anomaly_types': list(anomaly_explanations.keys()),
            'explanations': anomaly_explanations,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': (total + page_size - 1) // page_size
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/clustering', methods=['GET'])
def get_clustering_data():
    """Get clustering analysis data with enhanced information"""
    try:
        clustering_data = data_service.get_clustering_data()
        
        if clustering_data.empty:
            return jsonify({
                'success': False,
                'error': 'No clustering data available'
            }), 404
        
        # Get cluster statistics
        cluster_stats = {}
        cluster_descriptions = {
            -1: 'Outliers - Objects that don\'t fit into any cluster',
            0: 'Main cluster - Objects with typical characteristics',
            1: 'Secondary cluster - Objects with similar orbital properties',
            2: 'Tertiary cluster - Specialized group'
        }
        
        # Calculate statistics for each cluster
        for cluster_id in clustering_data['cluster'].unique():
            cluster_objects = clustering_data[clustering_data['cluster'] == cluster_id]
            
            # Basic stats
            stats = {
                'count': len(cluster_objects),
                'description': cluster_descriptions.get(cluster_id, f'Cluster {cluster_id}'),
                'categories': cluster_objects['ui_category'].value_counts().to_dict(),
                'avg_radius': cluster_objects['mean_radius_km'].mean() if 'mean_radius_km' in cluster_objects else None,
                'avg_eccentricity': cluster_objects['eccentricity'].mean() if 'eccentricity' in cluster_objects else None,
                'avg_inclination': cluster_objects['inclination_deg'].mean() if 'inclination_deg' in cluster_objects else None
            }
            
            # Remove None values
            stats = {k: v for k, v in stats.items() if v is not None}
            
            cluster_stats[int(cluster_id)] = stats
        
        # Get PCA explained variance (if available)
        pca_info = {
            'component_1': 'Primary variance - typically related to size and orbital distance',
            'component_2': 'Secondary variance - typically related to orbital eccentricity and inclination'
        }
        
        # Prepare scatter plot data
        scatter_data = []
        for _, row in clustering_data.iterrows():
            point = {
                'id': row['id'],
                'name': row['display_name'] if 'display_name' in row else row['name'],
                'x': float(row['pca_1']) if pd.notna(row.get('pca_1')) else 0,
                'y': float(row['pca_2']) if pd.notna(row.get('pca_2')) else 0,
                'cluster': int(row['cluster']),
                'category': row.get('ui_category', 'Unknown'),
                'radius': float(row['mean_radius_km']) if pd.notna(row.get('mean_radius_km')) else None,
                'rarity': float(row['rarity_score']) if pd.notna(row.get('rarity_score')) else None
            }
            scatter_data.append(point)
        
        # Get bounds for visualization
        pca_bounds = {
            'x_min': clustering_data['pca_1'].min(),
            'x_max': clustering_data['pca_1'].max(),
            'y_min': clustering_data['pca_2'].min(),
            'y_max': clustering_data['pca_2'].max()
        }
        
        return jsonify({
            'success': True,
            'total_objects': len(clustering_data),
            'num_clusters': len(clustering_data['cluster'].unique()),
            'cluster_stats': cluster_stats,
            'pca_info': pca_info,
            'pca_bounds': pca_bounds,
            'scatter_data': scatter_data,
            'data': dataframe_to_json_safe(clustering_data)  # Keep raw data for compatibility
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
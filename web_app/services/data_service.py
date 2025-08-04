import pandas as pd
import json
from pathlib import Path
from typing import Optional, List, Dict

from config import Config

class DataService:
    """Service for handling local CSV/JSON data operations"""
    
    def __init__(self):
        self.data_dir = Config.DATA_DIR
        self._main_objects_df = None
        self._anomalies_df = None
        self._clustering_df = None
        self._image_mapping = None
    
    @property
    def main_objects(self):
        """Lazy load main objects data"""
        if self._main_objects_df is None:
            # Define dtypes for problematic columns
            dtype_spec = {
                'id': str,
                'name': str,
                'object_type': str,
                'is_planet': str,
                'discovered_by': str,
                'discovery_date': str,
                'has_image': str,
                'is_neo': str,
                'is_pha': str,
                'is_anomaly': str
            }
            
            self._main_objects_df = pd.read_csv(
                self.data_dir / 'main_objects.csv',
                dtype=dtype_spec,
                low_memory=False
            )
            
            # Convert boolean columns
            bool_columns = ['is_planet', 'has_image', 'is_neo', 'is_pha', 'is_anomaly']
            for col in bool_columns:
                if col in self._main_objects_df.columns:
                    self._main_objects_df[col] = self._main_objects_df[col].map(
                        {'True': True, 'False': False, 'true': True, 'false': False}
                    ).fillna(False)
                    
        return self._main_objects_df
    
    @property
    def anomalies(self):
        """Lazy load anomalies data"""
        if self._anomalies_df is None:
            dtype_spec = {
                'id': str,
                'name': str,
                'object_type': str,
                'is_planet': str,
                'has_image': str,
                'is_anomaly': str,
                'anomaly_type': str
            }
            
            self._anomalies_df = pd.read_csv(
                self.data_dir / 'anomaly_objects.csv',
                dtype=dtype_spec,
                low_memory=False
            )
            
            # Convert boolean columns
            bool_columns = ['is_planet', 'has_image', 'is_anomaly']
            for col in bool_columns:
                if col in self._anomalies_df.columns:
                    self._anomalies_df[col] = self._anomalies_df[col].map(
                        {'True': True, 'False': False, 'true': True, 'false': False}
                    ).fillna(False)
                    
        return self._anomalies_df
    
    @property
    def clustering_data(self):
        """Lazy load clustering data"""
        if self._clustering_df is None:
            try:
                self._clustering_df = pd.read_csv(self.data_dir / 'clustering_objects.csv')
            except FileNotFoundError:
                self._clustering_df = pd.DataFrame()
        return self._clustering_df
    
    @property
    def image_mapping(self):
        """Lazy load image mapping"""
        if self._image_mapping is None:
            try:
                with open(self.data_dir / 'image_mapping.json', 'r') as f:
                    self._image_mapping = json.load(f)
            except FileNotFoundError:
                self._image_mapping = {}
        return self._image_mapping
    
    def get_objects(self, category: Optional[str] = None, 
                   has_anomaly: bool = False,
                   min_radius: Optional[float] = None,
                   max_radius: Optional[float] = None,
                   search: Optional[str] = None) -> pd.DataFrame:
        """Get filtered objects from main dataset"""
        df = self.main_objects.copy()
        
        # Apply filters
        if category:
            df = df[df['ui_category'] == category]
        
        if has_anomaly:
            # Check if object has is_anomaly flag or is in anomalies list
            if 'is_anomaly' in df.columns:
                df = df[df['is_anomaly'] == True]
            else:
                anomaly_ids = self.anomalies['id'].unique()
                df = df[df['id'].isin(anomaly_ids)]
        
        if min_radius is not None:
            # Handle both mean_radius_km and diameter_km
            radius_mask = pd.Series([False] * len(df), index=df.index)
            if 'mean_radius_km' in df.columns:
                radius_mask |= (df['mean_radius_km'] >= min_radius)
            if 'diameter_km' in df.columns:
                radius_mask |= (df['diameter_km'] / 2 >= min_radius)
            df = df[radius_mask]
        
        if max_radius is not None:
            # Handle both mean_radius_km and diameter_km
            radius_mask = pd.Series([True] * len(df), index=df.index)
            if 'mean_radius_km' in df.columns:
                radius_mask &= (df['mean_radius_km'] <= max_radius)
            if 'diameter_km' in df.columns:
                radius_mask &= (df['diameter_km'] / 2 <= max_radius)
            df = df[radius_mask]
        
        if search:
            search_lower = search.lower()
            mask = (
                df['name'].str.lower().str.contains(search_lower, na=False) |
                df['display_name'].str.lower().str.contains(search_lower, na=False) |
                df['search_keywords'].str.lower().str.contains(search_lower, na=False)
            )
            df = df[mask]
        
        return df
    
    def get_object_by_id(self, object_id: str) -> Optional[pd.Series]:
        """Get single object by ID"""
        try:
            # Try to find in main objects
            mask = self.main_objects['id'] == object_id
            if mask.any():
                return self.main_objects[mask].iloc[0]
            
            # Try numeric ID if string ID not found
            try:
                numeric_id = int(object_id)
                mask = self.main_objects['id'] == numeric_id
                if mask.any():
                    return self.main_objects[mask].iloc[0]
            except ValueError:
                pass
            
            return None
        except Exception:
            return None
    
    def get_anomalies(self) -> pd.DataFrame:
        """Get all anomalous objects"""
        return self.anomalies.copy()
    
    def get_clustering_data(self) -> pd.DataFrame:
        """Get clustering analysis data"""
        return self.clustering_data.copy()
    
    def get_local_image_path(self, object_id: str) -> Optional[str]:
        """Get local image path for an object if available"""
        # Check image mapping
        if str(object_id) in self.image_mapping:
            return self.image_mapping[str(object_id)]
        
        # Try alternative formats
        try:
            numeric_id = int(object_id)
            if str(numeric_id) in self.image_mapping:
                return self.image_mapping[str(numeric_id)]
        except ValueError:
            pass
        
        return None
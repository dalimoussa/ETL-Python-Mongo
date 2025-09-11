"""
Data transformer module for MongoDB ETL.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime

from config.config import VALIDATION_CONFIG

logger = logging.getLogger(__name__)

class DataTransformer:
    """
    Transform raw MongoDB data into structured formats for machine learning.
    
    This class provides methods to clean, normalize, and structure data
    extracted from MongoDB into formats optimized for machine learning.
    """
    
    def __init__(self, schema: Optional[Dict[str, Any]] = None):
        """
        Initialize the data transformer.
        
        Args:
            schema: Optional schema definition for validation and transformation
        """
        self.schema = schema
        self.missing_rate_threshold = VALIDATION_CONFIG['missing_rate_threshold']
        self.outlier_threshold = VALIDATION_CONFIG['outlier_threshold']
    
    def transform_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply standard transformations to a list of documents.
        
        Args:
            documents: List of MongoDB documents
            
        Returns:
            List of transformed documents
        """
        if not documents:
            return []
        
        # Convert to pandas DataFrame for efficient processing
        df = pd.DataFrame(documents)
        
        # Apply basic cleaning
        df = self._clean_dataframe(df)
        
        # Apply normalization
        df = self._normalize_dataframe(df)
        
        # Handle missing values
        df = self._handle_missing_values(df)
        
        # Detect and handle outliers
        df = self._handle_outliers(df)
        
        # Convert back to list of dictionaries
        return df.to_dict('records')
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean a DataFrame by removing duplicates and standardizing formats.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        # Drop complete duplicates
        initial_len = len(df)
        df = df.drop_duplicates()
        if len(df) < initial_len:
            logger.info(f"Removed {initial_len - len(df)} duplicate records")
        
        # Standardize string columns - strip whitespace
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].dtype == 'object' and df[col].apply(lambda x: isinstance(x, str)).all():
                df[col] = df[col].str.strip()
        
        # Convert timestamps to datetime objects
        for col in df.columns:
            # Check if column potentially contains timestamps
            if col.lower().endswith(('date', 'time', 'dt', 'timestamp')):
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    logger.debug(f"Converted {col} to datetime")
                except Exception as e:
                    logger.warning(f"Failed to convert {col} to datetime: {str(e)}")
        
        return df
    
    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize numerical fields in the DataFrame.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Normalized DataFrame
        """
        # Identify numerical columns to normalize
        numeric_cols = df.select_dtypes(include=['float', 'int']).columns
        
        # Skip normalization if no numeric columns or if DataFrame is empty
        if len(numeric_cols) == 0 or len(df) == 0:
            return df
        
        # Create a copy to avoid modifying the original DataFrame
        df_normalized = df.copy()
        
        for col in numeric_cols:
            # Skip columns with all zeros or all same value
            if df[col].std() == 0:
                continue
            
            # Create normalized column name
            normalized_col_name = f"{col}_normalized"
            
            # Apply min-max normalization
            min_val = df[col].min()
            max_val = df[col].max()
            
            if max_val > min_val:
                df_normalized[normalized_col_name] = (df[col] - min_val) / (max_val - min_val)
                logger.debug(f"Normalized column {col} to {normalized_col_name}")
        
        return df_normalized
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values in the DataFrame.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with handled missing values
        """
        # Calculate missing rate for each column
        missing_rates = df.isnull().mean()
        
        # Create a copy to avoid modifying the original DataFrame
        df_clean = df.copy()
        
        for col, missing_rate in missing_rates.items():
            # Skip if missing rate is below threshold
            if missing_rate == 0:
                continue
            
            # Log columns with high missing rates
            if missing_rate > self.missing_rate_threshold:
                logger.warning(f"Column '{col}' has {missing_rate:.2%} missing values, above threshold {self.missing_rate_threshold:.2%}")
            
            # Handle missing values based on data type
            if pd.api.types.is_numeric_dtype(df[col]):
                # For numeric columns, fill with median
                median_val = df[col].median()
                df_clean[col] = df[col].fillna(median_val)
                logger.debug(f"Filled missing values in column '{col}' with median {median_val}")
                
                # Add indicator column for missing values
                df_clean[f"{col}_missing"] = df[col].isnull().astype(int)
            
            elif pd.api.types.is_datetime64_dtype(df[col]):
                # For datetime, fill with mode or leave as null
                if not df[col].dropna().empty:
                    mode_val = df[col].mode()[0]
                    df_clean[col] = df[col].fillna(mode_val)
                    logger.debug(f"Filled missing datetime values in column '{col}' with mode")
            
            else:
                # For categorical/string columns, fill with 'UNKNOWN'
                df_clean[col] = df[col].fillna('UNKNOWN')
                logger.debug(f"Filled missing values in column '{col}' with 'UNKNOWN'")
        
        return df_clean
    
    def _handle_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect and handle outliers in numerical columns.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with handled outliers
        """
        # Only process numeric columns
        numeric_cols = df.select_dtypes(include=['float', 'int']).columns
        
        # Create a copy to avoid modifying the original DataFrame
        df_clean = df.copy()
        
        for col in numeric_cols:
            # Skip if column has too few unique values
            if df[col].nunique() < 5:
                continue
            
            # Calculate Z-scores
            mean_val = df[col].mean()
            std_val = df[col].std()
            
            if std_val == 0:
                continue
                
            z_scores = (df[col] - mean_val) / std_val
            
            # Identify outliers
            outliers = (abs(z_scores) > self.outlier_threshold)
            outlier_count = outliers.sum()
            
            if outlier_count > 0:
                logger.info(f"Detected {outlier_count} outliers in column '{col}'")
                
                # Create outlier indicator column
                df_clean[f"{col}_outlier"] = outliers.astype(int)
                
                # Cap outliers at threshold value
                lower_bound = mean_val - self.outlier_threshold * std_val
                upper_bound = mean_val + self.outlier_threshold * std_val
                
                df_clean[col] = df_clean[col].clip(lower=lower_bound, upper=upper_bound)
                logger.debug(f"Capped outliers in column '{col}' to range [{lower_bound:.3f}, {upper_bound:.3f}]")
        
        return df_clean
    
    def flatten_nested_documents(self, documents: List[Dict[str, Any]], 
                                max_depth: int = 3) -> List[Dict[str, Any]]:
        """
        Flatten nested documents for machine learning algorithms.
        
        Args:
            documents: List of MongoDB documents
            max_depth: Maximum depth to flatten
            
        Returns:
            List of flattened documents
        """
        flattened_docs = []
        
        for doc in documents:
            flattened_doc = {}
            self._flatten_dict(doc, flattened_doc, prefix='', depth=0, max_depth=max_depth)
            flattened_docs.append(flattened_doc)
        
        return flattened_docs
    
    def _flatten_dict(self, nested_dict: Dict[str, Any], 
                     flattened_dict: Dict[str, Any], 
                     prefix: str, 
                     depth: int, 
                     max_depth: int) -> None:
        """
        Recursively flatten a nested dictionary.
        
        Args:
            nested_dict: The nested dictionary to flatten
            flattened_dict: The result dictionary to populate
            prefix: Current key prefix
            depth: Current recursion depth
            max_depth: Maximum recursion depth
        """
        if depth >= max_depth:
            # Reached maximum depth, store the value as is
            if prefix:
                flattened_dict[prefix] = nested_dict
            return
        
        for key, value in nested_dict.items():
            new_key = f"{prefix}_{key}" if prefix else key
            
            if isinstance(value, dict):
                # Recursively flatten nested dictionaries
                self._flatten_dict(value, flattened_dict, new_key, depth + 1, max_depth)
            elif isinstance(value, list):
                # Handle lists of dictionaries or primitive values
                if value and all(isinstance(item, dict) for item in value):
                    # List of dictionaries: create numbered keys
                    for i, item in enumerate(value):
                        item_key = f"{new_key}_{i}"
                        if isinstance(item, dict):
                            self._flatten_dict(item, flattened_dict, item_key, depth + 1, max_depth)
                        else:
                            flattened_dict[item_key] = item
                else:
                    # List of primitive values or mixed: store as is
                    flattened_dict[new_key] = value
            else:
                # Regular key-value pair
                flattened_dict[new_key] = value
    
    def process_geospatial_features(self, documents: List[Dict[str, Any]], 
                                   geo_field: str,
                                   reference_point: Optional[List[float]] = None) -> List[Dict[str, Any]]:
        """
        Process geospatial features to create ML-friendly features.
        
        Args:
            documents: List of MongoDB documents with geospatial data
            geo_field: Field containing geospatial data
            reference_point: Optional reference point for distance calculations
            
        Returns:
            List of documents with additional geospatial features
        """
        processed_docs = []
        
        for doc in documents:
            processed_doc = doc.copy()
            
            # Extract coordinates
            coords = self._extract_coordinates(doc, geo_field)
            
            if coords:
                # Add individual lat/lon columns for ML models
                processed_doc[f"{geo_field}_lon"] = coords[0]
                processed_doc[f"{geo_field}_lat"] = coords[1]
                
                # Calculate distance from reference point if provided
                if reference_point and len(reference_point) == 2:
                    distance = self._haversine_distance(
                        coords[1], coords[0],
                        reference_point[1], reference_point[0]
                    )
                    processed_doc[f"distance_to_reference"] = distance
            
            processed_docs.append(processed_doc)
        
        return processed_docs
    
    def _extract_coordinates(self, doc: Dict[str, Any], geo_field: str) -> Optional[List[float]]:
        """
        Extract coordinates from a document's geospatial field.
        
        Args:
            doc: MongoDB document
            geo_field: Field containing geospatial data
            
        Returns:
            [longitude, latitude] coordinates or None if not found
        """
        if geo_field not in doc:
            return None
        
        geo_data = doc[geo_field]
        
        # Handle GeoJSON Point format
        if isinstance(geo_data, dict) and geo_data.get('type') == 'Point' and 'coordinates' in geo_data:
            return geo_data['coordinates']
        
        # Handle array format [lon, lat]
        elif isinstance(geo_data, list) and len(geo_data) >= 2:
            return [float(geo_data[0]), float(geo_data[1])]
        
        # Handle nested object with lat/lon properties
        elif isinstance(geo_data, dict) and 'lon' in geo_data and 'lat' in geo_data:
            return [float(geo_data['lon']), float(geo_data['lat'])]
        
        # Handle nested object with longitude/latitude properties
        elif isinstance(geo_data, dict) and 'longitude' in geo_data and 'latitude' in geo_data:
            return [float(geo_data['longitude']), float(geo_data['latitude'])]
        
        return None
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great-circle distance between two points on Earth.
        
        Args:
            lat1: Latitude of point 1 in degrees
            lon1: Longitude of point 1 in degrees
            lat2: Latitude of point 2 in degrees
            lon2: Longitude of point 2 in degrees
            
        Returns:
            Distance in kilometers
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        r = 6371  # Earth radius in kilometers
        
        return c * r

"""
Data validation module for MongoDB ETL.
"""

import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)

class DataValidator:
    """
    Validate data integrity for ETL pipeline.
    
    This class provides methods to validate data against schemas,
    check for inconsistencies, and generate data quality reports.
    """
    
    def __init__(self, schema: Optional[Dict[str, Any]] = None):
        """
        Initialize the data validator.
        
        Args:
            schema: Optional JSON schema for validation
        """
        self.schema = schema
    
    def load_schema_from_file(self, schema_path: str) -> None:
        """
        Load JSON schema from a file.
        
        Args:
            schema_path: Path to the schema file
        """
        try:
            with open(schema_path, 'r') as f:
                self.schema = json.load(f)
            logger.info(f"Loaded schema from {schema_path}")
        except Exception as e:
            logger.error(f"Failed to load schema from {schema_path}: {str(e)}")
            raise
    
    def validate_schema(self, documents: List[Dict[str, Any]], 
                       max_errors: int = 10) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate documents against JSON schema.
        
        Args:
            documents: List of documents to validate
            max_errors: Maximum number of errors to collect
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        if not self.schema:
            logger.warning("No schema provided for validation")
            return False, [{"error": "No schema provided"}]
        
        errors = []
        valid = True
        
        for i, doc in enumerate(documents):
            try:
                validate(instance=doc, schema=self.schema)
            except ValidationError as e:
                valid = False
                error_info = {
                    "document_index": i,
                    "error_message": str(e),
                    "error_path": list(e.path),
                    "error_schema_path": list(e.schema_path),
                }
                errors.append(error_info)
                
                if len(errors) >= max_errors:
                    logger.warning(f"Reached maximum error count ({max_errors}), stopping validation")
                    break
        
        if valid:
            logger.info(f"All {len(documents)} documents passed schema validation")
        else:
            logger.error(f"Schema validation failed with {len(errors)} errors")
        
        return valid, errors
    
    def generate_data_profile(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a data profile with statistics and quality metrics.
        
        Args:
            documents: List of documents to profile
            
        Returns:
            Dictionary with data profile information
        """
        if not documents:
            return {"error": "No documents provided for profiling"}
        
        # Convert to DataFrame for efficient analysis
        df = pd.DataFrame(documents)
        
        profile = {
            "record_count": len(df),
            "column_count": len(df.columns),
            "columns": {},
            "missing_values": {},
            "statistics": {},
            "potential_issues": []
        }
        
        # Generate column-level profiles
        for col in df.columns:
            col_profile = self._profile_column(df, col)
            profile["columns"][col] = col_profile
        
        # Overall missing value analysis
        missing_counts = df.isnull().sum()
        for col in df.columns:
            missing_count = missing_counts[col]
            if missing_count > 0:
                missing_rate = missing_count / len(df)
                profile["missing_values"][col] = {
                    "count": int(missing_count),
                    "rate": float(missing_rate)
                }
                
                # Flag high missing rates
                if missing_rate > 0.1:  # 10% threshold
                    profile["potential_issues"].append({
                        "type": "high_missing_rate",
                        "column": col,
                        "missing_rate": float(missing_rate),
                        "severity": "high" if missing_rate > 0.5 else "medium"
                    })
        
        # Duplicate analysis
        duplicate_count = len(df) - len(df.drop_duplicates())
        if duplicate_count > 0:
            profile["duplicate_records"] = {
                "count": duplicate_count,
                "rate": float(duplicate_count / len(df))
            }
            
            if duplicate_count / len(df) > 0.05:  # 5% threshold
                profile["potential_issues"].append({
                    "type": "high_duplicate_rate",
                    "count": duplicate_count,
                    "rate": float(duplicate_count / len(df)),
                    "severity": "medium"
                })
        
        # Date range analysis for date columns
        for col in df.columns:
            if pd.api.types.is_datetime64_dtype(df[col]):
                min_date = df[col].min()
                max_date = df[col].max()
                
                if not pd.isna(min_date) and not pd.isna(max_date):
                    profile["statistics"][f"{col}_date_range"] = {
                        "min": min_date.isoformat(),
                        "max": max_date.isoformat(),
                        "span_days": (max_date - min_date).days
                    }
        
        return profile
    
    def _profile_column(self, df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """
        Generate a profile for a single column.
        
        Args:
            df: DataFrame containing the data
            column: Name of the column to profile
            
        Returns:
            Dictionary with column profile
        """
        profile = {
            "data_type": str(df[column].dtype),
            "unique_count": int(df[column].nunique())
        }
        
        # Calculate statistics based on data type
        if pd.api.types.is_numeric_dtype(df[column]):
            # Numeric column
            numeric_stats = {
                "min": float(df[column].min()) if not df[column].empty else None,
                "max": float(df[column].max()) if not df[column].empty else None,
                "mean": float(df[column].mean()) if not df[column].empty else None,
                "median": float(df[column].median()) if not df[column].empty else None,
                "std": float(df[column].std()) if not df[column].empty else None,
            }
            profile.update(numeric_stats)
            
            # Check for outliers
            if not df[column].empty and df[column].nunique() > 1:
                q1 = float(df[column].quantile(0.25))
                q3 = float(df[column].quantile(0.75))
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                outlier_count = ((df[column] < lower_bound) | (df[column] > upper_bound)).sum()
                
                profile["outliers"] = {
                    "count": int(outlier_count),
                    "rate": float(outlier_count / len(df)),
                    "lower_bound": lower_bound,
                    "upper_bound": upper_bound
                }
                
        elif pd.api.types.is_string_dtype(df[column]) or df[column].dtype == 'object':
            # String or object column
            non_null_values = df[column].dropna()
            
            if not non_null_values.empty:
                # Get value frequency
                value_counts = df[column].value_counts()
                top_value = value_counts.index[0] if not value_counts.empty else None
                top_count = value_counts.iloc[0] if not value_counts.empty else 0
                
                string_stats = {
                    "top_value": str(top_value) if top_value is not None else None,
                    "top_count": int(top_count),
                    "top_frequency": float(top_count / len(df)) if top_count > 0 else 0
                }
                profile.update(string_stats)
                
                # Check for potential categorical column (few unique values)
                if 1 < non_null_values.nunique() <= 10:  # Between 2 and 10 unique values
                    profile["potential_categorical"] = True
                    profile["categories"] = list(non_null_values.unique())
        
        # Add cardinality indicator
        cardinality_ratio = df[column].nunique() / len(df) if len(df) > 0 else 0
        profile["cardinality_ratio"] = float(cardinality_ratio)
        
        if cardinality_ratio == 1.0:
            profile["unique_identifier"] = True
        
        return profile
    
    def validate_geospatial_data(self, documents: List[Dict[str, Any]], 
                                geo_field: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate geospatial data in documents.
        
        Args:
            documents: List of documents to validate
            geo_field: Field containing geospatial data
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        valid = True
        
        for i, doc in enumerate(documents):
            # Check if the geo field exists
            if geo_field not in doc:
                valid = False
                errors.append({
                    "document_index": i,
                    "error_type": "missing_field",
                    "message": f"Geospatial field '{geo_field}' is missing"
                })
                continue
            
            geo_data = doc[geo_field]
            
            # Validate GeoJSON Point format
            if isinstance(geo_data, dict) and geo_data.get('type') == 'Point' and 'coordinates' in geo_data:
                coords = geo_data['coordinates']
                if not self._validate_coordinates(coords):
                    valid = False
                    errors.append({
                        "document_index": i,
                        "error_type": "invalid_coordinates",
                        "message": f"Invalid coordinates in GeoJSON Point: {coords}"
                    })
                    
            # Validate array format [lon, lat]
            elif isinstance(geo_data, list):
                if not self._validate_coordinates(geo_data):
                    valid = False
                    errors.append({
                        "document_index": i,
                        "error_type": "invalid_coordinates",
                        "message": f"Invalid coordinate array: {geo_data}"
                    })
                    
            # Validate object with lat/lon or longitude/latitude properties
            elif isinstance(geo_data, dict) and (
                ('lon' in geo_data and 'lat' in geo_data) or 
                ('longitude' in geo_data and 'latitude' in geo_data)
            ):
                if 'lon' in geo_data and 'lat' in geo_data:
                    coords = [geo_data['lon'], geo_data['lat']]
                else:
                    coords = [geo_data['longitude'], geo_data['latitude']]
                
                if not self._validate_coordinates(coords):
                    valid = False
                    errors.append({
                        "document_index": i,
                        "error_type": "invalid_coordinates",
                        "message": f"Invalid coordinates in object: {geo_data}"
                    })
            else:
                valid = False
                errors.append({
                    "document_index": i,
                    "error_type": "invalid_format",
                    "message": f"Unrecognized geospatial format: {geo_data}"
                })
        
        return valid, errors
    
    def _validate_coordinates(self, coords: List[float]) -> bool:
        """
        Validate longitude and latitude coordinates.
        
        Args:
            coords: [longitude, latitude] coordinates
            
        Returns:
            True if coordinates are valid, False otherwise
        """
        if not isinstance(coords, list) or len(coords) < 2:
            return False
        
        try:
            lon = float(coords[0])
            lat = float(coords[1])
            
            # Check longitude range: -180 to 180
            if lon < -180 or lon > 180:
                return False
            
            # Check latitude range: -90 to 90
            if lat < -90 or lat > 90:
                return False
            
            return True
        except (ValueError, TypeError):
            return False
    
    def check_data_distribution(self, documents: List[Dict[str, Any]], 
                              column: str,
                              reference_distribution: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Check the distribution of values in a column against a reference distribution.
        
        Args:
            documents: List of documents to check
            column: Column to analyze
            reference_distribution: Optional reference distribution to compare against
            
        Returns:
            Dictionary with distribution information
        """
        # Convert to DataFrame
        df = pd.DataFrame(documents)
        
        if column not in df.columns:
            return {
                "error": f"Column '{column}' not found in the data"
            }
        
        # Calculate actual distribution
        value_counts = df[column].value_counts(normalize=True).to_dict()
        
        results = {
            "column": column,
            "actual_distribution": value_counts
        }
        
        # Compare with reference distribution if provided
        if reference_distribution:
            # Calculate JS divergence
            results["reference_distribution"] = reference_distribution
            
            # Calculate KL divergence (an approximation for this use case)
            kl_divergence = 0
            for value, ref_prob in reference_distribution.items():
                actual_prob = value_counts.get(value, 0)
                # Avoid division by zero by adding a small epsilon
                if actual_prob > 0 and ref_prob > 0:
                    kl_divergence += actual_prob * np.log(actual_prob / ref_prob)
            
            results["kl_divergence"] = float(kl_divergence)
            results["distribution_shift_detected"] = kl_divergence > 0.1  # Threshold for significance
        
        return results

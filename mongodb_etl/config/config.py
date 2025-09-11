"""
Configuration settings for MongoDB ETL pipeline.
"""

from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB connection settings
MONGODB_CONFIG = {
    'uri': os.getenv('MONGODB_URI', 'mongodb://localhost:27017'),
    'database': os.getenv('MONGODB_DATABASE', 'raw_data'),
    'read_preference': 'secondaryPreferred',  # Optimize for read-heavy operations
    'max_pool_size': 100,                    # Connection pool size for parallel processing
    'timeout_ms': 30000,                     # 30 seconds timeout
    'retry_writes': True,                    # Auto-retry for write operations
}

# Output formats configuration
OUTPUT_FORMATS = {
    'json': {
        'indent': 2,
        'orient': 'records',
    },
    'csv': {
        'delimiter': ',',
        'quotechar': '"',
        'encoding': 'utf-8',
    },
    'parquet': {
        'compression': 'snappy',
        'row_group_size': 100000,
    }
}

# Processing configuration
PROCESSING_CONFIG = {
    'batch_size': 10000,          # Number of documents to process in a single batch
    'max_workers': os.cpu_count() or 4,  # Maximum number of parallel workers
    'log_level': os.getenv('LOG_LEVEL', 'INFO'),
}

# Validation thresholds
VALIDATION_CONFIG = {
    'missing_rate_threshold': 0.05,  # Maximum allowed rate of missing values (5%)
    'outlier_threshold': 3.0,        # Z-score threshold for outlier detection
    'schema_validation': True,       # Enforce schema validation
}

# Geospatial settings
GEOSPATIAL_CONFIG = {
    'coordinate_precision': 6,       # Decimal places for coordinates
    'default_distance_unit': 'km',   # Default unit for distance calculations
    'default_max_distance': 5,       # Default maximum distance for $near queries (in km)
}

def get_collection_config(collection_name: str) -> Dict[str, Any]:
    """
    Get collection-specific configuration.
    
    Args:
        collection_name: Name of the MongoDB collection
        
    Returns:
        Dictionary with collection-specific configuration
    """
    # Collection-specific configurations can be defined here
    collection_configs = {
        'locations': {
            'geo_field': 'coordinates',
            'index_type': '2dsphere',
        },
        'users': {
            'sensitive_fields': ['email', 'phone', 'ssn'],
            'anonymize': True,
        }
    }
    
    return collection_configs.get(collection_name, {})

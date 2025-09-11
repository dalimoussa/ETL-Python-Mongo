"""
Example usage of the MongoDB ETL pipeline.
"""

import os
import logging
import time
from typing import Dict, List, Any

# Import ETL components
from mongodb_etl import MongoDBETL
from mongodb_etl.extractors.geo_extractor import GeoSpatialExtractor
from mongodb_etl.transformers.data_transformer import DataTransformer
from mongodb_etl.loaders.data_loader import DataLoader
from mongodb_etl.validators.data_validator import DataValidator
from mongodb_etl.utils.performance_utils import (
    timer_decorator,
    memory_usage_decorator,
    log_pipeline_metrics
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ETLRunner:
    """
    Example runner for MongoDB ETL pipeline.
    
    This class demonstrates how to use the ETL components
    to extract, transform, and load data from MongoDB.
    """
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the ETL runner.
        
        Args:
            output_dir: Directory to save output files
        """
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    @timer_decorator
    @memory_usage_decorator
    def run_basic_etl_pipeline(self, 
                             collection_name: str, 
                             query: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run a basic ETL pipeline.
        
        Args:
            collection_name: Name of the MongoDB collection
            query: Optional query to filter documents
            
        Returns:
            Dictionary with pipeline metrics
        """
        # Initialize ETL components
        etl = MongoDBETL(collection_name)
        transformer = DataTransformer()
        loader = DataLoader(self.output_dir)
        
        # Extract data
        start_time = time.time()
        cursor = etl.extract(query)
        
        # Define transformation function
        def transform_func(docs):
            return transformer.transform_documents(docs)
        
        # Define load function
        def load_func(transformed_docs):
            loader.save_to_multiple_formats(
                transformed_docs,
                f"{collection_name}_processed",
                formats=["json", "csv", "parquet"]
            )
        
        # Process data in batches
        stats = etl.process_in_batches(cursor, transform_func, load_func)
        
        # Add pipeline metrics
        stats["total_pipeline_time"] = time.time() - start_time
        
        # Close MongoDB connection
        etl.close()
        
        # Log metrics
        log_pipeline_metrics(stats, f"basic_etl_{collection_name}")
        
        return stats
    
    @timer_decorator
    @memory_usage_decorator
    def run_geospatial_etl_pipeline(self,
                                  collection_name: str,
                                  geo_field: str,
                                  point: List[float],
                                  max_distance: float) -> Dict[str, Any]:
        """
        Run a geospatial ETL pipeline.
        
        Args:
            collection_name: Name of the MongoDB collection
            geo_field: Field containing geospatial data
            point: [longitude, latitude] coordinates for search
            max_distance: Maximum distance in meters
            
        Returns:
            Dictionary with pipeline metrics
        """
        # Initialize ETL components
        geo_extractor = GeoSpatialExtractor(collection_name, geo_field)
        transformer = DataTransformer()
        loader = DataLoader(self.output_dir)
        validator = DataValidator()
        
        # Extract data near a point
        start_time = time.time()
        cursor = geo_extractor.extract_near(point, max_distance)
        
        # Define transformation function with geospatial processing
        def transform_func(docs):
            # Transform documents with standard transformations
            transformed_docs = transformer.transform_documents(docs)
            
            # Add geospatial features
            return transformer.process_geospatial_features(transformed_docs, geo_field, point)
        
        # Define load function
        def load_func(transformed_docs):
            # Validate geospatial data
            is_valid, errors = validator.validate_geospatial_data(transformed_docs, geo_field)
            
            if not is_valid:
                logger.warning(f"Found {len(errors)} validation errors in geospatial data")
            
            # Save only valid documents
            valid_docs = [doc for i, doc in enumerate(transformed_docs) 
                         if i not in [e["document_index"] for e in errors]]
            
            # Split into train/val/test and save
            loader.split_and_save(
                valid_docs,
                f"{collection_name}_geo",
                format="parquet"
            )
        
        # Process data in parallel
        stats = geo_extractor.process_parallel(cursor, transform_func, load_func)
        
        # Add pipeline metrics
        stats["total_pipeline_time"] = time.time() - start_time
        
        # Close MongoDB connection
        geo_extractor.close()
        
        # Log metrics
        log_pipeline_metrics(stats, f"geo_etl_{collection_name}")
        
        return stats

# Example usage
if __name__ == "__main__":
    # Create ETL runner
    runner = ETLRunner("data/ml_datasets")
    
    # Run basic ETL pipeline
    logger.info("Running basic ETL pipeline...")
    basic_stats = runner.run_basic_etl_pipeline(
        "sample_collection",
        {"status": "active"}  # Optional query filter
    )
    logger.info(f"Basic ETL pipeline completed: {basic_stats}")
    
    # Run geospatial ETL pipeline
    logger.info("Running geospatial ETL pipeline...")
    geo_stats = runner.run_geospatial_etl_pipeline(
        "locations",
        "coordinates",
        [-73.9857, 40.7484],  # Example coordinates (NYC)
        5000  # 5 kilometers
    )
    logger.info(f"Geospatial ETL pipeline completed: {geo_stats}")

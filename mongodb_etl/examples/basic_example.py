"""
Example usage of the MongoDB ETL framework.

This script demonstrates how to use the MongoDB ETL framework
to extract, transform, and load data from MongoDB into formats
suitable for machine learning.
"""

import os
import logging
import json
from dotenv import load_dotenv

from mongodb_etl import MongoDBETL
from extractors.geo_extractor import GeoSpatialExtractor
from transformers.data_transformer import DataTransformer
from loaders.data_loader import DataLoader
from validators.data_validator import DataValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def basic_etl_example():
    """Basic ETL example."""
    logger.info("Running basic ETL example")
    
    # Create output directory
    output_dir = os.path.join(os.getcwd(), "example_output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize ETL components
    etl = MongoDBETL("sample_collection")
    transformer = DataTransformer()
    loader = DataLoader(output_dir)
    
    try:
        # Extract data
        logger.info("Extracting data")
        cursor = etl.extract({"status": "active"})
        
        # Process in batches
        def transform_func(docs):
            return transformer.transform_documents(docs)
        
        def load_func(transformed_docs):
            loader.save_to_multiple_formats(
                transformed_docs, 
                "example_output",
                ["json", "csv"]
            )
        
        # Process data
        stats = etl.process_in_batches(cursor, transform_func, load_func)
        
        logger.info(f"Processed {stats['docs_processed']} documents")
        
    finally:
        # Close MongoDB connection
        etl.close()

def geospatial_etl_example():
    """Geospatial ETL example."""
    logger.info("Running geospatial ETL example")
    
    # Create output directory
    output_dir = os.path.join(os.getcwd(), "example_output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize ETL components
    geo_extractor = GeoSpatialExtractor("locations", "coordinates")
    transformer = DataTransformer()
    loader = DataLoader(output_dir)
    validator = DataValidator()
    
    try:
        # Extract data near a point (New York City)
        logger.info("Extracting geospatial data")
        cursor = geo_extractor.extract_near(
            point=[-73.9857, 40.7484],  # NYC coordinates
            max_distance=5000  # 5 kilometers
        )
        
        # Process in parallel
        def transform_func(docs):
            # Transform documents
            transformed_docs = transformer.transform_documents(docs)
            
            # Add geospatial features
            return transformer.process_geospatial_features(
                transformed_docs, 
                "coordinates",
                [-73.9857, 40.7484]  # Reference point
            )
        
        def load_func(transformed_docs):
            # Validate geospatial data
            is_valid, errors = validator.validate_geospatial_data(
                transformed_docs, 
                "coordinates"
            )
            
            if not is_valid:
                logger.warning(f"Found {len(errors)} validation errors")
            
            # Split into train/val/test and save
            loader.split_and_save(
                transformed_docs,
                "geo_features",
                format="parquet"
            )
        
        # Process data
        stats = geo_extractor.process_parallel(cursor, transform_func, load_func)
        
        logger.info(f"Processed {stats['docs_processed']} documents in parallel")
        
    finally:
        # Close MongoDB connection
        geo_extractor.close()

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run examples
    try:
        basic_etl_example()
        geospatial_etl_example()
        
        logger.info("Examples completed successfully")
    except Exception as e:
        logger.error(f"Examples failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

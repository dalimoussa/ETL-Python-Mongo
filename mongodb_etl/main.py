"""
MongoDB ETL for Machine Learning - Main entry point.

This script provides a command-line interface for the MongoDB ETL framework.
It can be used to extract data from MongoDB, transform it, and load it into
various formats for machine learning.
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv
from datetime import datetime

from . import MongoDBETL
from .extractors.geo_extractor import GeoSpatialExtractor
from .transformers.data_transformer import DataTransformer
from .loaders.data_loader import DataLoader
from .validators.data_validator import DataValidator
from .utils.performance_utils import log_pipeline_metrics, timer_decorator

def setup_logging(log_level):
    """Set up logging."""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="MongoDB ETL Tool for Machine Learning")
    
    parser.add_argument("--collection", type=str, required=True, 
                        help="MongoDB collection name")
    
    parser.add_argument("--query", type=str, default="{}", 
                        help="MongoDB query as JSON string")
    
    parser.add_argument("--output-dir", type=str, default="output",
                        help="Directory to save output files")
    
    parser.add_argument("--output-format", type=str, choices=["json", "csv", "parquet", "all"], 
                        default="all", help="Output format")
    
    parser.add_argument("--output-name", type=str, default="mongodb_data",
                        help="Base name for output files")
    
    parser.add_argument("--batch-size", type=int, default=10000,
                        help="Batch size for processing")
    
    parser.add_argument("--parallel", action="store_true",
                        help="Use parallel processing")
    
    parser.add_argument("--geo-field", type=str, 
                        help="Field containing geospatial data")
    
    parser.add_argument("--split", action="store_true",
                        help="Split data into train/val/test sets")
    
    parser.add_argument("--log-level", type=str, default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Logging level")
    
    parser.add_argument("--validate", action="store_true",
                        help="Validate data integrity")
    
    return parser.parse_args()

@timer_decorator
def run_etl_pipeline(args, logger):
    """Run the ETL pipeline."""
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize ETL components
    etl = None
    transformer = DataTransformer()
    loader = DataLoader(args.output_dir)
    validator = DataValidator() if args.validate else None
    
    try:
        start_time = datetime.now()
        
        # Choose appropriate extractor based on args
        if args.geo_field:
            logger.info(f"Using geospatial extractor with field: {args.geo_field}")
            etl = GeoSpatialExtractor(args.collection, args.geo_field)
        else:
            logger.info(f"Using standard MongoDB ETL for collection: {args.collection}")
            etl = MongoDBETL(args.collection)
        
        # Parse query string
        import json
        query = json.loads(args.query)
        
        # Extract data
        logger.info(f"Extracting data with query: {query}")
        cursor = etl.extract(query)
        
        # Define transformation function
        def transform_func(docs):
            # Transform documents
            transformed = transformer.transform_documents(docs)
            
            # Add geospatial features if needed
            if args.geo_field:
                transformed = transformer.process_geospatial_features(transformed, args.geo_field)
            
            # Validate if requested
            if args.validate:
                valid, errors = validator.validate_geospatial_data(transformed, args.geo_field) if args.geo_field else (True, [])
                if not valid:
                    logger.warning(f"Found {len(errors)} validation errors")
            
            return transformed
        
        # Define load function
        def load_func(transformed_docs):
            if not transformed_docs:
                return
                
            if args.split:
                # Split and save data
                formats = []
                if args.output_format == "all" or args.output_format == "json":
                    formats.append("json")
                if args.output_format == "all" or args.output_format == "csv":
                    formats.append("csv")
                if args.output_format == "all" or args.output_format == "parquet":
                    formats.append("parquet")
                
                for fmt in formats:
                    logger.info(f"Splitting and saving data in {fmt} format")
                    loader.split_and_save(transformed_docs, args.output_name, fmt)
            else:
                # Save in requested formats
                formats = []
                if args.output_format == "all":
                    formats = ["json", "csv", "parquet"]
                else:
                    formats = [args.output_format]
                
                for fmt in formats:
                    logger.info(f"Saving data in {fmt} format")
                    if fmt == "json":
                        loader.save_to_json(transformed_docs, args.output_name)
                    elif fmt == "csv":
                        loader.save_to_csv(transformed_docs, args.output_name)
                    elif fmt == "parquet":
                        loader.save_to_parquet(transformed_docs, args.output_name)
        
        # Process data
        if args.parallel:
            logger.info(f"Processing data in parallel with batch size: {args.batch_size}")
            etl.batch_size = args.batch_size
            stats = etl.process_parallel(cursor, transform_func, load_func)
        else:
            logger.info(f"Processing data in batches with batch size: {args.batch_size}")
            etl.batch_size = args.batch_size
            stats = etl.process_in_batches(cursor, transform_func, load_func)
        
        # Add pipeline execution time
        end_time = datetime.now()
        stats["execution_time"] = str(end_time - start_time)
        
        # Log metrics
        log_pipeline_metrics(stats, f"etl_{args.collection}")
        
        logger.info(f"ETL pipeline completed successfully. Processed {stats.get('docs_processed', 0)} documents.")
        return stats
        
    finally:
        # Close MongoDB connection
        if etl:
            etl.close()

def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()
    
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    logger = setup_logging(args.log_level)
    
    try:
        # Run ETL pipeline
        stats = run_etl_pipeline(args, logger)
        return 0
    except Exception as e:
        logger.error(f"ETL pipeline failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())

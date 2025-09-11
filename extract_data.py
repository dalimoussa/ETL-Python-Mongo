"""
MongoDB ETL - Simple extraction script example

This script demonstrates how to use the MongoDB ETL package to extract data 
from your MongoDB database and save it to a file.

Usage:
    python extract_data.py

The output will be saved in the ./output_data directory.
"""
import os
import json
from datetime import datetime
from mongodb_etl import MongoDBETL
from mongodb_etl.transformers.data_transformer import DataTransformer
from mongodb_etl.loaders.data_loader import DataLoader

# Set up paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(CURRENT_DIR, "output_data")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Connect to your database
# Replace these values with your actual database connection info
etl = MongoDBETL(
    collection_name="your_collection",
    config={
        "uri": "mongodb://localhost:27017/",
        "database": "your_database_name"
    }
)

# Extract data with optional query filter
# Remove or modify the filter as needed
query_filter = {"status": "active"}
cursor = etl.extract(query_filter)

# Create transformer and loader
transformer = DataTransformer()
loader = DataLoader(OUTPUT_DIR)

# Process and save data
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"extracted_data_{timestamp}"

# Process in batches
stats = etl.process_in_batches(
    cursor,
    transform_func=transformer.transform_documents,
    load_func=lambda docs: loader.save_to_json(docs, filename)
)

# Print summary
print("\nExtraction Summary:")
print("-" * 50)
print(f"Documents processed: {stats['docs_processed']}")
print(f"Processing time: {stats['total_time_seconds']:.2f} seconds")
print(f"Output saved to: {os.path.abspath(os.path.join(OUTPUT_DIR, filename + '.json'))}")
print("\nData extraction complete!")

# Close the connection
etl.close()

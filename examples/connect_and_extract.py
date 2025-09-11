"""
Example script showing how to connect to your MongoDB database and extract data
"""
import os
from dotenv import load_dotenv
from mongodb_etl import MongoDBETL
from mongodb_etl.transformers.data_transformer import DataTransformer
from mongodb_etl.loaders.data_loader import DataLoader

# Load environment variables from .env file if present
load_dotenv()

# Get MongoDB connection details from environment variables or use defaults
mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
mongodb_db = os.getenv("MONGODB_DB", "your_database")
collection_name = "your_collection"  # Replace with your collection name

# Initialize ETL components
etl = MongoDBETL(
    collection_name=collection_name,
    config={
        "uri": mongodb_uri,
        "database": mongodb_db
    }
)

# Extract data (customize query filter as needed)
query_filter = {}  # Empty filter means "get all documents"
cursor = etl.extract(query_filter)

# Initialize transformer and loader
transformer = DataTransformer()
loader = DataLoader("./output_data")

# Define simple transformation function
def transform_data(documents):
    print(f"Transforming batch of {len(documents)} documents")
    return transformer.transform_documents(documents)

# Define simple load function
def save_data(transformed_docs):
    print(f"Saving {len(transformed_docs)} transformed documents")
    loader.save_to_json(transformed_docs, "extracted_data")

# Process data in batches (with progress reporting)
print(f"Starting extraction from {mongodb_db}.{collection_name}")
stats = etl.process_in_batches(
    cursor, 
    transform_func=transform_data,
    load_func=save_data,
    batch_size=100,
    show_progress=True
)

# Print summary
print(f"\nExtraction complete!")
print(f"Processed {stats['docs_processed']} documents")
print(f"Processing time: {stats['total_time_seconds']:.2f} seconds")
print(f"Output directory: {os.path.abspath('./output_data')}")

# Close MongoDB connection
etl.close()

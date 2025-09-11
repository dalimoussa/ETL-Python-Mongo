"""
Example script for extracting MongoDB data with geospatial filtering
"""
import os
from dotenv import load_dotenv
from mongodb_etl.extractors.geo_extractor import GeoSpatialExtractor
from mongodb_etl.transformers.data_transformer import DataTransformer
from mongodb_etl.loaders.data_loader import DataLoader

# Load environment variables from .env file if present
load_dotenv()

# Get MongoDB connection details from environment variables or use defaults
mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
mongodb_db = os.getenv("MONGODB_DB", "your_database")
collection_name = "locations"  # Replace with your geospatial collection name
geo_field = "coordinates"      # Field containing GeoJSON coordinates

# Initialize geospatial extractor
geo_extractor = GeoSpatialExtractor(
    collection_name=collection_name,
    geo_field=geo_field,
    config={
        "uri": mongodb_uri,
        "database": mongodb_db
    }
)

# Set up reference point (example: Manhattan, NYC)
reference_point = [-73.9857, 40.7484]  # [longitude, latitude]
max_distance = 5000  # 5 kilometers

print(f"Extracting locations within {max_distance}m of {reference_point}")

# Extract locations near the reference point
cursor = geo_extractor.extract_near(
    point=reference_point,
    max_distance=max_distance
)

# Initialize transformer and loader
transformer = DataTransformer()
output_dir = "./geo_output"
loader = DataLoader(output_dir)

# Define transformation function that adds distance calculations
def transform_geo_data(documents):
    # Apply standard transformations
    transformed = transformer.transform_documents(documents)
    
    # Add geospatial features like distance from reference point
    return transformer.process_geospatial_features(
        transformed, 
        geo_field,
        reference_point
    )

# Define load function that saves to both CSV and GeoJSON
def save_geo_data(transformed_docs):
    # Save as GeoJSON for mapping applications
    loader.save_to_json(transformed_docs, "geo_results")
    
    # Also save as CSV for analysis
    loader.save_to_csv(transformed_docs, "geo_results")
    
    return transformed_docs

# Process data
stats = geo_extractor.process_in_batches(
    cursor,
    transform_func=transform_geo_data,
    load_func=save_geo_data,
    batch_size=100,
    show_progress=True
)

# Print summary
print(f"\nExtraction complete!")
print(f"Found {stats['docs_processed']} locations within {max_distance}m")
print(f"Processing time: {stats['total_time_seconds']:.2f} seconds")
print(f"Output saved to: {os.path.abspath(output_dir)}")

# Close connection
geo_extractor.close()

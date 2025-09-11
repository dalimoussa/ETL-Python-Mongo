# MongoDB ETL

![Build Status](https://img.shields.io/github/workflow/status/yourusername/mongodb-etl/Python%20ETL%20Tests)
![Python Version](https://img.shields.io/badge/python-3.8%20|%203.9%20|%203.10%20|%203.11%20|%203.12-blue)
![License](https://img.shields.io/github/license/yourusername/mongodb-etl)

High-performance Python ETL framework for transforming MongoDB data into structured datasets for machine learning.

## Features

- **MongoDB Integration** - Optimized data extraction with geospatial query support
- **Parallel Processing** - Process data in batches or parallel for optimal performance
- **Flexible Transformations** - Data cleaning, normalization, and feature engineering
- **Multiple Output Formats** - Export to JSON, CSV, and Parquet formats
- **ML-Ready Datasets** - Automatic train/validation/test splitting
- **Validation & Testing** - Data quality validation and schema verification
- **Modular Architecture** - Easy to extend and customize components

## Installation

### Quick Install

```bash
pip install git+https://github.com/yourusername/mongodb-etl.git
```

### Development Install

```bash
git clone https://github.com/yourusername/mongodb-etl.git
cd mongodb-etl
pip install -e .
```

### Requirements

- Python 3.8+
- MongoDB 4.0+
- Dependencies:
  - pymongo
  - pandas
  - numpy
  - pyarrow (for Parquet support)

## Usage

### Command-Line Interface

The package provides a command-line interface for easy use:

```bash
# Basic usage
python -m mongodb_etl.main --collection your_collection --output-dir output

# With query filter
python -m mongodb_etl.main --collection your_collection --query '{"status": "active"}' --output-format json

# Geospatial data
python -m mongodb_etl.main --collection locations --geo-field coordinates --parallel --split
```

### Basic ETL Pipeline

```python
from mongodb_etl import MongoDBETL
from mongodb_etl.transformers.data_transformer import DataTransformer
from mongodb_etl.loaders.data_loader import DataLoader

# Initialize ETL components
etl = MongoDBETL("your_collection")
transformer = DataTransformer()
loader = DataLoader("output_directory")

# Extract data
cursor = etl.extract({"status": "active"})

# Define transformation function
def transform_func(docs):
    return transformer.transform_documents(docs)

# Define load function
def load_func(transformed_docs):
    loader.save_to_json(transformed_docs, "processed_data")

# Process data in batches
stats = etl.process_in_batches(cursor, transform_func, load_func)
print(f"Processed {stats['docs_processed']} documents")

# Close MongoDB connection
etl.close()
```

### Geospatial ETL Pipeline

```python
from mongodb_etl.extractors.geo_extractor import GeoSpatialExtractor
from mongodb_etl.transformers.data_transformer import DataTransformer
from mongodb_etl.loaders.data_loader import DataLoader

# Initialize geospatial extractor
geo_extractor = GeoSpatialExtractor("locations", "coordinates")

# Extract locations near a point (longitude, latitude)
cursor = geo_extractor.extract_near(
    point=[-73.9857, 40.7484],  # NYC coordinates
    max_distance=5000  # 5 kilometers
)

# Define transformation function
def transform_func(docs):
    # Apply standard transformations
    transformed_docs = transformer.transform_documents(docs)
    
    # Add geospatial features
    return transformer.process_geospatial_features(
        transformed_docs, 
        "coordinates",
        [-73.9857, 40.7484]  # Reference point
    )

# Define load function
def load_func(transformed_docs):
    loader.save_to_parquet(transformed_docs, "geo_features")

# Process data in parallel
transformer = DataTransformer()
loader = DataLoader("ml_datasets")
stats = geo_extractor.process_parallel(cursor, transform_func, load_func)

print(f"Processed {stats['docs_processed']} documents in {stats['total_time_seconds']:.2f}s")
```

### Data Validation

```python
from mongodb_etl.validators.data_validator import DataValidator

# Initialize validator
validator = DataValidator()

# Load schema from file
validator.load_schema_from_file("schemas/data_schema.json")

# Validate data against schema
is_valid, errors = validator.validate_schema(documents)
if not is_valid:
    print(f"Found {len(errors)} schema validation errors")
    
# Generate data profile
profile = validator.generate_data_profile(documents)
print(f"Data profile: {profile}")
```

## Project Structure

```
mongodb_etl/
├── __init__.py
├── config.py
├── main.py
├── mongodb_etl.py
├── extractors/
│   ├── __init__.py
│   └── geo_extractor.py
├── transformers/
│   ├── __init__.py
│   └── data_transformer.py
├── loaders/
│   ├── __init__.py
│   └── data_loader.py
├── validators/
│   ├── __init__.py
│   └── data_validator.py
├── utils/
│   ├── __init__.py
│   └── performance_utils.py
├── examples/
│   ├── basic_example.py
│   └── geospatial_example.py
└── tests/
    ├── __init__.py
    ├── test_mongodb_etl.py
    └── test_integration.py
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

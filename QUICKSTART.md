# Quick Start Guide for MongoDB ETL

This guide will help you set up and use the MongoDB ETL tool with your own database.

## 1. Setup and Installation

### Clone and Install

```powershell
# Clone the repository
git clone https://github.com/dalimoussa/mongodb-etl.git
cd mongodb-etl

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\Activate.ps1

# Install the package
pip install -e .
```

### Configure MongoDB Connection

By default, the tool uses these connection settings:
- Host: localhost
- Port: 27017
- No authentication

For custom connections, create a `.env` file in your project root:

```
# .env file
MONGODB_URI=mongodb://username:password@hostname:port/
MONGODB_DB=your_database_name
```

Or set environment variables directly:

```powershell
$env:MONGODB_URI = "mongodb://username:password@hostname:port/"
$env:MONGODB_DB = "your_database_name"
```

## 2. Extract Data - Quick Examples

### Command-Line Approach

The simplest way to extract data is using the command-line interface:

```powershell
# Basic extraction to JSON files
python -m mongodb_etl.main --collection your_collection --output-dir ./output

# Extract with query filter
python -m mongodb_etl.main --collection your_collection --query '{"status":"active"}' --output-format json

# Extract to CSV with specific fields
python -m mongodb_etl.main --collection your_collection --fields "name,email,age" --output-format csv
```

### Python Script Approach

For more flexibility, you can write your own Python script. Follow these steps:

1. Create a new file called `extract_data.py` in your project directory:
   ```powershell
   # Navigate to your project directory
   cd C:\Users\medal\Downloads\test
   
   # Create the script using your preferred editor
   notepad extract_data.py
   ```

2. Copy and paste the following code into `extract_data.py`:

```python
from mongodb_etl import MongoDBETL
from mongodb_etl.transformers.data_transformer import DataTransformer
from mongodb_etl.loaders.data_loader import DataLoader

# Connect to your database
etl = MongoDBETL(
    collection_name="your_collection",
    config={
        "uri": "mongodb://username:password@hostname:port/",
        "database": "your_database_name"
    }
)

# Extract data with optional query filter
cursor = etl.extract({"status": "active"})

# Create transformer and loader
transformer = DataTransformer()
loader = DataLoader("./output_data")

# Process and save data
etl.process_in_batches(
    cursor,
    transform_func=transformer.transform_documents,
    load_func=lambda docs: loader.save_to_json(docs, "extracted_data")
)

print("Data extraction complete!")
```

3. Save the file and then run it:
```powershell
# Make sure your virtual environment is activated
.\venv\Scripts\Activate.ps1

# Run the script
python extract_data.py
```

4. The extracted data will be saved in the `output_data` folder in your current directory:
```
C:\Users\medal\Downloads\test\output_data\extracted_data.json
```

## 3. Customizing Extraction

### Filter Data

Filter the documents you extract:

```python
# Extract only documents matching specific criteria
cursor = etl.extract({"category": "product", "price": {"$gt": 100}})
```

### Transform Data

Apply custom transformations:

```python
def my_transform_function(documents):
    transformed = []
    for doc in documents:
        # Add calculated fields
        doc["full_name"] = f"{doc.get('first_name', '')} {doc.get('last_name', '')}"
        
        # Remove sensitive fields
        if "password" in doc:
            del doc["password"]
            
        transformed.append(doc)
    return transformed

# Use custom transformation
etl.process_in_batches(cursor, my_transform_function, load_func)
```

### Export Options

Save data in different formats:

```python
# JSON format
loader.save_to_json(transformed_data, "output_filename")

# CSV format
loader.save_to_csv(transformed_data, "output_filename")

# Parquet format (efficient for ML)
loader.save_to_parquet(transformed_data, "output_filename")

# Split into train/validation/test sets
loader.split_and_save(
    transformed_data, 
    "ml_dataset",
    format="parquet",
    train_ratio=0.7,
    val_ratio=0.15,
    test_ratio=0.15
)
```

## Need Help?

See the [full documentation](README.md) for more advanced features or open an issue on GitHub for assistance.

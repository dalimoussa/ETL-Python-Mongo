# Quick Start Guide# Quick Start Guide



Get your MongoDB data extracted and ready for analysis in 5 minutes.Get your MongoDB data extracted and ready for analysis in 5 minutes.



## Step 1: Setup## Step 1: Setup



```powershell```powershell

# Clone the project# Clone the project

git clone https://github.com/dalimoussa/ETL-Python-Mongo.gitgit clone https://github.com/dalimoussa/ETL-Python-Mongo.git

cd ETL-Python-Mongocd ETL-Python-Mongo



# Create and activate virtual environment# Create and activate virtual environment

python -m venv .venvpython -m venv .venv

.\.venv\Scripts\Activate.ps1.\.venv\Scripts\Activate.ps1



# Install the tool# Install the tool

pip install -e .pip install -e .

``````



## Step 2: Start the Visual Interface## Step 2: Start the Visual Interface



```powershell```powershell

mongodb-etl-guimongodb-etl-gui

``````



The window will open with 5 tabs:The window will open with 5 tabs:



### Connection Tab### Connection Tab

- **MongoDB URI**: `mongodb://localhost:27017/` (change if needed)- **MongoDB URI**: `mongodb://localhost:27017/` (change if needed)

- Click **Connect** button- Click **Connect** button

- Select your **database** from dropdown- Select your **database** from dropdown



### Data Selection Tab  ### Data Selection Tab  

- Choose your **collection** from dropdown- Choose your **collection** from dropdown

- **Query Filter**: `{}` (empty = all data, or use `{"field":"value"}`)- **Query Filter**: `{}` (empty = all data, or use `{"field":"value"}`)

- **Limit**: `0` (0 = all records, or set a number like 1000)- **Limit**: `0` (0 = all records, or set a number like 1000)



### Output Settings Tab### Output Settings Tab

- **Output Directory**: Choose where to save files- **Output Directory**: Choose where to save files

- **Format**: Pick JSON, CSV, or Parquet- **Format**: Pick JSON, CSV, or Parquet

- **Split Data**: Check this to create train/validation/test files- **Split Data**: Check this to create train/validation/test files



### Run ETL Tab### Run ETL Tab

- Click **Run ETL Process**- Click **Run ETL Process**

- Watch the progress bar and logs- Watch the progress bar and logs

- Get success message when done- Get success message when done



### Output Viewer Tab### Output Viewer Tab

- See your exported data automatically- See your exported data automatically

- Refresh to view files again- Refresh to view files again



## Step 3: Command Line (Alternative)## Step 3: Command Line (Alternative)



If you prefer command line:If you prefer command line:



```powershell```powershell

# Basic extraction to JSON files# Basic extraction to JSON files

mongodb-etl --collection your_collection --output-dir ./outputpython -m mongodb_etl.main --collection your_collection --output-dir ./output



# Extract with query filter# Extract with query filter

mongodb-etl --collection your_collection --query '{"status":"active"}' --output-format jsonpython -m mongodb_etl.main --collection your_collection --query '{"status":"active"}' --output-format json



# Extract to CSV# Extract to CSV with specific fields

mongodb-etl --collection your_collection --output-format csv --output-dir ./outputpython -m mongodb_etl.main --collection your_collection --fields "name,email,age" --output-format csv

``````



## Step 4: Configuration (Optional)### Python Script Approach



For different databases, create a `.env` file:For more flexibility, you can write your own Python script. Follow these steps:



```1. Create a new file called `extract_data.py` in your project directory:

MONGODB_URI=mongodb://username:password@hostname:port/   ```powershell

MONGODB_DATABASE=your_database_name   # Navigate to your project directory

```   cd C:\Users\User\Downloads\test

   

Or set environment variables:   # Create the script using your preferred editor

   notepad extract_data.py

```powershell   ```

$env:MONGODB_URI = "mongodb://username:password@hostname:port/"

$env:MONGODB_DATABASE = "your_database_name"2. Copy and paste the following code into `extract_data.py`:

```

```python

## Examplesfrom mongodb_etl import MongoDBETL

from mongodb_etl.transformers.data_transformer import DataTransformer

### Extract all productsfrom mongodb_etl.loaders.data_loader import DataLoader

```powershell

mongodb-etl --collection products --output-dir ./data# Connect to your database

```etl = MongoDBETL(

    collection_name="your_collection",

### Extract recent orders to CSV    config={

```powershell        "uri": "mongodb://username:password@hostname:port/",

mongodb-etl --collection orders --query '{"date":{"$gte":"2024-01-01"}}' --output-format csv        "database": "your_database_name"

```    }

)

### Create ML training data

```powershell# Extract data with optional query filter

mongodb-etl --collection customers --split --output-format parquetcursor = etl.extract({"status": "active"})

```

# Create transformer and loader

## Need Help?transformer = DataTransformer()

loader = DataLoader("./output_data")

- **GUI won't start**: Try `python -m mongodb_etl.gui`

- **Connection issues**: Check your `.env` file or MongoDB server# Process and save data

- **Python not found**: Make sure virtual environment is activatedetl.process_in_batches(

    cursor,

See the [full documentation](README.md) for advanced features.    transform_func=transformer.transform_documents,
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

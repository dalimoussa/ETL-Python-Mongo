# MongoDB ETL Tool

A simple Python tool to extract data from MongoDB and save it in different formats (JSON, CSV, Parquet) for data analysis and machine learning.

## What it does

- Connects to MongoDB and extracts data from collections
- Cleans and transforms your data automatically 
- Saves data in formats ready for analysis (JSON, CSV, Parquet)
- Splits data into training/validation/test sets for machine learning
- Works with both a visual interface (GUI) and command line
- Handles geospatial data and complex queries

## Quick Start

### 1. Install

```bash
# Clone the project
git clone https://github.com/dalimoussa/ETL-Python-Mongo.git
cd ETL-Python-Mongo

# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows)
.\.venv\Scripts\Activate.ps1

# Install the tool
pip install -e .
```

### 2. Run the Visual Interface (Easiest)

```bash
mongodb-etl-gui
```

1. **Connect**: Enter your MongoDB connection details
2. **Select Data**: Choose a collection and set filters  
3. **Choose Output**: Pick format (JSON/CSV/Parquet) and location
4. **Run**: Click "Run ETL Process" and wait for completion

### 3. Use Command Line

```bash
# Show all options
mongodb-etl --help

# Extract a collection to JSON
mongodb-etl --collection my_collection --output-dir ./results

# Extract with filters to CSV
mongodb-etl --collection users --query '{"status":"active"}' --output-format csv
```

## Configuration

The tool connects to `mongodb://localhost:27017` by default. To use a different database:

### Option 1: Environment File
Create a `.env` file in the project folder:
```
MONGODB_URI=mongodb://username:password@your-server:27017
MONGODB_DATABASE=your_database_name
```

### Option 2: Set Environment Variables
```bash
# Windows PowerShell
$env:MONGODB_URI = "mongodb://username:password@your-server:27017"
$env:MONGODB_DATABASE = "your_database_name"
```

## Common Use Cases

### Extract all data from a collection
```bash
mongodb-etl --collection products --output-dir ./data
```

### Extract with filters
```bash
mongodb-etl --collection orders --query '{"date":{"$gte":"2024-01-01"}}' --output-format csv
```

### Create ML training sets
```bash
mongodb-etl --collection customers --split --output-format parquet
```
This creates train.parquet, validation.parquet, and test.parquet files.

### Work with location data
```bash
mongodb-etl --collection stores --geo-field coordinates --output-format json
```

## Requirements

- Python 3.8 or newer
- MongoDB database (local or remote)
- Windows, Mac, or Linux

## Troubleshooting

**"Python was not found"**: Make sure you activated the virtual environment first:
```bash
.\.venv\Scripts\Activate.ps1
```

**Can't connect to MongoDB**: Check your connection string in the `.env` file or environment variables.

**GUI won't start**: Try the module version:
```bash
python -m mongodb_etl.gui
```

## Project Structure

```
mongodb_etl/
├── extractors/     # MongoDB data extraction
├── transformers/   # Data cleaning and processing  
├── loaders/        # Save data in different formats
├── validators/     # Data quality checks
└── examples/       # Sample scripts
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

MIT License - see [LICENSE](LICENSE) file.

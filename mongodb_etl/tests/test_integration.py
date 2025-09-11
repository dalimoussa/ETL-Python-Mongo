"""
Integration tests for the MongoDB ETL pipeline.

These tests require a running MongoDB instance.
"""

import unittest
import os
import sys
import logging
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import pymongo
from pymongo import MongoClient

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mongodb_etl import MongoDBETL
from transformers.data_transformer import DataTransformer
from loaders.data_loader import DataLoader

# Disable logging for tests
logging.basicConfig(level=logging.ERROR)

class IntegrationTests(unittest.TestCase):
    """Integration tests for MongoDB ETL pipeline."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        load_dotenv()
        cls.uri = os.getenv('MONGODB_URI')
        cls.db_name = os.getenv('MONGODB_DATABASE')
        cls.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "output")
        os.makedirs(cls.output_dir, exist_ok=True)
        
        try:
            # Connect to MongoDB
            cls.client = MongoClient(cls.uri)
            cls.db = cls.client[cls.db_name]
            # Ensure MongoDB is running
            cls.client.admin.command('ping')
            cls.setup_test_data()
        except Exception as e:
            raise unittest.SkipTest(f"MongoDB not available: {str(e)}")
    
    @classmethod
    def setup_test_data(cls):
        """Set up test data in MongoDB."""
        # Create test collection
        cls.collection_name = "integration_test_collection"
        if cls.collection_name in cls.db.list_collection_names():
            cls.db[cls.collection_name].drop()
        
        # Create sample data
        cls.sample_data = [
            {
                "name": "Sample 1",
                "value": 10,
                "timestamp": datetime.now(),
                "status": "active",
                "nested": {"field1": "value1", "field2": 42},
                "coordinates": {"type": "Point", "coordinates": [-73.9857, 40.7484]}
            },
            {
                "name": "Sample 2",
                "value": 20,
                "timestamp": datetime.now(),
                "status": "active",
                "nested": {"field1": "value2", "field2": 84},
                "coordinates": {"type": "Point", "coordinates": [-118.2437, 34.0522]}
            },
            {
                "name": "Sample 3",
                "value": 30,
                "timestamp": datetime.now(),
                "status": "inactive",
                "nested": {"field1": "value3", "field2": 126},
                "coordinates": {"type": "Point", "coordinates": [-87.6298, 41.8781]}
            }
        ]
        
        # Insert data
        result = cls.db[cls.collection_name].insert_many(cls.sample_data)
        cls.inserted_ids = result.inserted_ids
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        if hasattr(cls, 'client') and cls.client:
            # Drop test collection
            if hasattr(cls, 'collection_name') and cls.collection_name:
                if cls.collection_name in cls.db.list_collection_names():
                    cls.db[cls.collection_name].drop()
            
            # Close MongoDB connection
            cls.client.close()
            
    def test_extraction(self):
        """Test data extraction."""
        etl = MongoDBETL(self.collection_name)
        cursor = etl.extract()
        documents = list(cursor)
        
        self.assertEqual(len(documents), 3)
        self.assertEqual(documents[0]["name"], "Sample 1")
        self.assertEqual(documents[1]["name"], "Sample 2")
        self.assertEqual(documents[2]["name"], "Sample 3")
        etl.close()
    
    def test_filtered_extraction(self):
        """Test filtered data extraction."""
        etl = MongoDBETL(self.collection_name)
        cursor = etl.extract({"status": "active"})
        documents = list(cursor)
        
        self.assertEqual(len(documents), 2)
        statuses = [doc["status"] for doc in documents]
        self.assertTrue(all(status == "active" for status in statuses))
        etl.close()
    
    def test_transformation(self):
        """Test data transformation."""
        etl = MongoDBETL(self.collection_name)
        cursor = etl.extract()
        documents = list(cursor)
        
        transformer = DataTransformer()
        transformed_data = transformer.transform_documents(documents)
        
        self.assertEqual(len(transformed_data), 3)
        self.assertTrue("value_normalized" in transformed_data[0])
        etl.close()
    
    def test_loading(self):
        """Test data loading."""
        etl = MongoDBETL(self.collection_name)
        cursor = etl.extract()
        documents = list(cursor)
        
        loader = DataLoader(self.output_dir)
        json_path = loader.save_to_json(documents, "test_integration")
        csv_path = loader.save_to_csv(documents, "test_integration")
        
        self.assertTrue(os.path.exists(json_path))
        self.assertTrue(os.path.exists(csv_path))
        
        # Check content
        df = pd.read_csv(csv_path)
        self.assertEqual(len(df), 3)
        
        etl.close()
        
        # Clean up test files
        if os.path.exists(json_path):
            os.remove(json_path)
        if os.path.exists(csv_path):
            os.remove(csv_path)

if __name__ == "__main__":
    unittest.main()

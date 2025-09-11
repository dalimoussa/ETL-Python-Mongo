"""
Unit tests for MongoDB ETL base class.
"""
import unittest
import os
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv
import sys
import pymongo

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mongodb_etl import MongoDBETL
from config.config import MONGODB_CONFIG

class TestMongoDBETL(unittest.TestCase):
    """Test cases for MongoDBETL class."""
    
    @patch('mongodb_etl.MongoClient')
    def test_connection(self, mock_client):
        """Test MongoDB connection."""
        # Setup mock
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_client.return_value = mock_db
        mock_db.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value.__getitem__.return_value = mock_collection
        
        # Create ETL instance
        etl = MongoDBETL("test_collection")
        
        # Verify
        mock_client.assert_called_once()
        self.assertEqual(etl.collection_name, "test_collection")
        self.assertIsNotNone(etl.client)
        self.assertIsNotNone(etl.db)
        self.assertIsNotNone(etl.collection)
    
    @patch('mongodb_etl.MongoClient')
    def test_extract(self, mock_client):
        """Test extract method."""
        # Setup mock
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_cursor = MagicMock()
        mock_client.return_value = mock_db
        mock_db.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value.__getitem__.return_value = mock_collection
        mock_collection.find.return_value = mock_cursor
        
        # Create ETL instance and call extract
        etl = MongoDBETL("test_collection")
        result = etl.extract({"status": "active"})
        
        # Verify
        mock_collection.find.assert_called_with({"status": "active"}, {})
        self.assertEqual(result, mock_cursor)
    
    @patch('mongodb_etl.MongoClient')
    def test_close(self, mock_client):
        """Test close method."""
        # Setup mock
        mock_db = MagicMock()
        mock_client.return_value = mock_db
        mock_db.__getitem__.return_value = mock_db
        
        # Create ETL instance and call close
        etl = MongoDBETL("test_collection")
        etl.close()
        
        # Verify
        mock_db.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()

"""
Main ETL module providing the core ETL functionality.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union, Callable
import pymongo
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.cursor import Cursor
from concurrent.futures import ThreadPoolExecutor, as_completed

from config.config import MONGODB_CONFIG, PROCESSING_CONFIG

# Configure logging
logging.basicConfig(
    level=getattr(logging, PROCESSING_CONFIG['log_level']),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MongoDBETL:
    """
    Base class for MongoDB ETL operations.
    
    This class provides the core functionality for extracting data from MongoDB,
    transforming it, and loading it into various output formats.
    """
    
    def __init__(self, collection_name: str, custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the ETL pipeline.
        
        Args:
            collection_name: Name of the MongoDB collection
            custom_config: Optional custom configuration to override defaults
        """
        self.config = {**MONGODB_CONFIG}
        if custom_config:
            self.config.update(custom_config)
        
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
        self.batch_size = PROCESSING_CONFIG['batch_size']
        self.max_workers = PROCESSING_CONFIG['max_workers']
        
        # Connect to MongoDB
        self._connect()
        
    def _connect(self) -> None:
        """Establish connection to MongoDB."""
        try:
            # Extract connection parameters properly
            uri = self.config.get('uri')
            database = self.config.get('database')
            
            # Connect using the URI string
            self.client = MongoClient(uri)
            self.db = self.client[database]
            self.collection = self.db[self.collection_name]
            logger.info(f"Connected to MongoDB collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    def extract(self, query: Dict[str, Any] = None, projection: Dict[str, Any] = None) -> Cursor:
        """
        Extract data from MongoDB collection.
        
        Args:
            query: MongoDB query to filter documents
            projection: Fields to include/exclude in the result
            
        Returns:
            MongoDB cursor for the query results
        """
        query = query or {}
        projection = projection or {}
        
        try:
            start_time = time.time()
            cursor = self.collection.find(query, projection)
            logger.info(f"Extracted data with query {query} in {time.time() - start_time:.2f}s")
            return cursor
        except Exception as e:
            logger.error(f"Failed to extract data: {str(e)}")
            raise
    
    def extract_with_geospatial(self, 
                               geo_query: Dict[str, Any],
                               additional_filters: Dict[str, Any] = None,
                               projection: Dict[str, Any] = None) -> Cursor:
        """
        Extract data using geospatial query operators.
        
        Args:
            geo_query: MongoDB geospatial query (using $near, $geoWithin, $geoIntersects)
            additional_filters: Additional query filters
            projection: Fields to include/exclude in the result
            
        Returns:
            MongoDB cursor for the query results
        """
        query = geo_query
        if additional_filters:
            query.update(additional_filters)
        
        projection = projection or {}
        
        try:
            start_time = time.time()
            cursor = self.collection.find(query, projection)
            logger.info(f"Extracted geospatial data in {time.time() - start_time:.2f}s")
            return cursor
        except Exception as e:
            logger.error(f"Failed to extract geospatial data: {str(e)}")
            raise
    
    def transform(self, data: List[Dict[str, Any]], 
                 transformation_func: Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Transform extracted data using the provided transformation function.
        
        Args:
            data: List of documents to transform
            transformation_func: Function to apply for transformation
            
        Returns:
            Transformed data
        """
        try:
            start_time = time.time()
            transformed_data = transformation_func(data)
            logger.info(f"Transformed {len(data)} documents in {time.time() - start_time:.2f}s")
            return transformed_data
        except Exception as e:
            logger.error(f"Failed to transform data: {str(e)}")
            raise
    
    def process_in_batches(self, 
                          cursor: Cursor, 
                          transform_func: Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]],
                          load_func: Callable[[List[Dict[str, Any]]], None]) -> Dict[str, Any]:
        """
        Process data in batches for memory efficiency.
        
        Args:
            cursor: MongoDB cursor with the data
            transform_func: Function to transform each batch
            load_func: Function to load each transformed batch
            
        Returns:
            Dictionary with processing statistics
        """
        start_time = time.time()
        batch_count = 0
        doc_count = 0
        
        try:
            current_batch = []
            
            for doc in cursor:
                current_batch.append(doc)
                doc_count += 1
                
                if len(current_batch) >= self.batch_size:
                    transformed_batch = self.transform(current_batch, transform_func)
                    load_func(transformed_batch)
                    batch_count += 1
                    current_batch = []
            
            # Process the last batch if it has any documents
            if current_batch:
                transformed_batch = self.transform(current_batch, transform_func)
                load_func(transformed_batch)
                batch_count += 1
            
            elapsed_time = time.time() - start_time
            stats = {
                "docs_processed": doc_count,
                "batch_count": batch_count,
                "total_time_seconds": elapsed_time,
                "docs_per_second": doc_count / elapsed_time if elapsed_time > 0 else 0
            }
            
            logger.info(f"Processed {doc_count} documents in {elapsed_time:.2f}s ({stats['docs_per_second']:.2f} docs/s)")
            return stats
        
        except Exception as e:
            logger.error(f"Failed to process in batches: {str(e)}")
            raise
    
    def process_parallel(self,
                        cursor: Cursor,
                        transform_func: Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]],
                        load_func: Callable[[List[Dict[str, Any]]], None]) -> Dict[str, Any]:
        """
        Process data in parallel using multiple workers.
        
        Args:
            cursor: MongoDB cursor with the data
            transform_func: Function to transform each batch
            load_func: Function to load each transformed batch
            
        Returns:
            Dictionary with processing statistics
        """
        start_time = time.time()
        batch_count = 0
        doc_count = 0
        
        try:
            # Group documents into batches
            batches = []
            current_batch = []
            
            for doc in cursor:
                current_batch.append(doc)
                doc_count += 1
                
                if len(current_batch) >= self.batch_size:
                    batches.append(current_batch)
                    batch_count += 1
                    current_batch = []
            
            # Add the last batch if not empty
            if current_batch:
                batches.append(current_batch)
                batch_count += 1
            
            # Process batches in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_batch = {
                    executor.submit(self._process_single_batch, batch, transform_func, load_func): i 
                    for i, batch in enumerate(batches)
                }
                
                # Process results as they complete
                for future in as_completed(future_to_batch):
                    batch_index = future_to_batch[future]
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Error processing batch {batch_index}: {str(e)}")
            
            elapsed_time = time.time() - start_time
            stats = {
                "docs_processed": doc_count,
                "batch_count": batch_count,
                "total_time_seconds": elapsed_time,
                "docs_per_second": doc_count / elapsed_time if elapsed_time > 0 else 0,
                "workers_used": min(batch_count, self.max_workers)
            }
            
            logger.info(f"Parallel processed {doc_count} documents in {elapsed_time:.2f}s "
                       f"({stats['docs_per_second']:.2f} docs/s) using {stats['workers_used']} workers")
            return stats
        
        except Exception as e:
            logger.error(f"Failed to process in parallel: {str(e)}")
            raise
    
    def _process_single_batch(self, 
                             batch: List[Dict[str, Any]], 
                             transform_func: Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]],
                             load_func: Callable[[List[Dict[str, Any]]], None]) -> None:
        """
        Process a single batch of documents.
        
        Args:
            batch: List of documents to process
            transform_func: Function to transform the batch
            load_func: Function to load the transformed batch
        """
        transformed_batch = self.transform(batch, transform_func)
        load_func(transformed_batch)
    
    def close(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

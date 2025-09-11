"""
Utility functions for MongoDB ETL.
"""

import time
import logging
import os
import psutil
import json
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from functools import wraps
from datetime import datetime
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.cursor import Cursor

logger = logging.getLogger(__name__)

def timer_decorator(func):
    """
    Decorator to measure execution time of a function.
    
    Args:
        func: Function to measure
        
    Returns:
        Wrapped function with timing
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Function {func.__name__} executed in {execution_time:.4f} seconds")
        return result
    return wrapper

def memory_usage_decorator(func):
    """
    Decorator to measure memory usage of a function.
    
    Args:
        func: Function to measure
        
    Returns:
        Wrapped function with memory usage tracking
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get memory usage before function call
        process = psutil.Process(os.getpid())
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        result = func(*args, **kwargs)
        
        # Get memory usage after function call
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_diff = end_memory - start_memory
        
        logger.info(f"Function {func.__name__} used {memory_diff:.2f} MB of memory")
        return result
    return wrapper

def estimate_document_size(document: Dict[str, Any]) -> int:
    """
    Estimate the size of a MongoDB document in bytes.
    
    Args:
        document: MongoDB document
        
    Returns:
        Estimated size in bytes
    """
    # Convert to JSON string and get byte length as an approximation
    return len(json.dumps(document).encode('utf-8'))

def estimate_batch_memory(documents: List[Dict[str, Any]]) -> float:
    """
    Estimate the memory usage of a batch of documents in MB.
    
    Args:
        documents: List of MongoDB documents
        
    Returns:
        Estimated memory usage in MB
    """
    if not documents:
        return 0.0
    
    # Sample size for large batches
    sample_size = min(len(documents), 100)
    
    # Calculate average size from sample
    sample_docs = documents[:sample_size]
    total_size_bytes = sum(estimate_document_size(doc) for doc in sample_docs)
    avg_size_bytes = total_size_bytes / sample_size
    
    # Estimate total batch size
    estimated_total_bytes = avg_size_bytes * len(documents)
    
    # Convert to MB
    return estimated_total_bytes / (1024 * 1024)

def optimize_batch_size(documents: List[Dict[str, Any]], 
                        initial_batch_size: int, 
                        max_memory_per_batch_mb: float = 100.0) -> int:
    """
    Optimize batch size based on document size and memory constraints.
    
    Args:
        documents: List of MongoDB documents
        initial_batch_size: Initial batch size
        max_memory_per_batch_mb: Maximum memory per batch in MB
        
    Returns:
        Optimized batch size
    """
    if not documents:
        return initial_batch_size
    
    # Sample documents
    sample_size = min(len(documents), 100)
    sample_docs = documents[:sample_size]
    
    # Calculate average document size
    avg_doc_size_bytes = sum(estimate_document_size(doc) for doc in sample_docs) / sample_size
    
    # Calculate batch size based on memory constraint
    max_batch_size = int(max_memory_per_batch_mb * 1024 * 1024 / avg_doc_size_bytes)
    
    # Use the smaller of initial batch size and max batch size
    optimized_size = min(initial_batch_size, max_batch_size)
    
    logger.info(f"Optimized batch size: {optimized_size} (avg doc size: {avg_doc_size_bytes/1024:.2f} KB)")
    return max(optimized_size, 1)  # Ensure at least batch size 1

def create_mongodb_index(collection: Collection, 
                        field: str, 
                        index_type: str = '1',  # '1' for ascending, '-1' for descending, '2dsphere' for geospatial
                        background: bool = True) -> None:
    """
    Create an index on a MongoDB collection.
    
    Args:
        collection: MongoDB collection
        field: Field to index
        index_type: Type of index
        background: Whether to create the index in the background
    """
    try:
        index_name = collection.create_index(
            [(field, index_type)],
            background=background
        )
        logger.info(f"Created index '{index_name}' on field '{field}'")
    except Exception as e:
        logger.error(f"Failed to create index on '{field}': {str(e)}")
        raise

def optimize_mongodb_query(collection: Collection, 
                         query: Dict[str, Any],
                         projection: Optional[Dict[str, Any]] = None,
                         sort_fields: Optional[List[Tuple[str, int]]] = None) -> Cursor:
    """
    Execute an optimized MongoDB query.
    
    Args:
        collection: MongoDB collection
        query: Query filter
        projection: Fields to include/exclude
        sort_fields: Fields to sort by
        
    Returns:
        MongoDB cursor with optimized query
    """
    # Add query optimization hints
    optimized_query = collection.find(
        filter=query,
        projection=projection,
        hint=sort_fields[0][0] if sort_fields else None,
        sort=sort_fields if sort_fields else None
    )
    
    return optimized_query

def log_pipeline_metrics(metrics: Dict[str, Any], 
                        pipeline_name: str,
                        output_file: Optional[str] = None) -> None:
    """
    Log ETL pipeline metrics.
    
    Args:
        metrics: Dictionary with metrics
        pipeline_name: Name of the pipeline
        output_file: Optional file to write metrics to
    """
    # Add timestamp
    metrics['timestamp'] = datetime.now().isoformat()
    metrics['pipeline_name'] = pipeline_name
    
    # Log metrics
    logger.info(f"Pipeline metrics for '{pipeline_name}': {json.dumps(metrics, indent=2)}")
    
    # Write to file if specified
    if output_file:
        try:
            mode = 'a' if os.path.exists(output_file) else 'w'
            with open(output_file, mode) as f:
                f.write(json.dumps(metrics) + '\n')
        except Exception as e:
            logger.error(f"Failed to write metrics to file '{output_file}': {str(e)}")

def chunks(lst: List[Any], n: int) -> List[List[Any]]:
    """
    Split a list into chunks of size n.
    
    Args:
        lst: List to split
        n: Chunk size
        
    Returns:
        List of chunks
    """
    return [lst[i:i + n] for i in range(0, len(lst), n)]

"""
Data loader module for MongoDB ETL.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
import pandas as pd

from config.config import OUTPUT_FORMATS

logger = logging.getLogger(__name__)

class DataLoader:
    """
    Base class for loading transformed data into various output formats.
    
    This class provides methods to save data in formats optimized
    for machine learning pipelines, including JSON, CSV, and Parquet.
    """
    
    def __init__(self, output_dir: str):
        """
        Initialize the data loader.
        
        Args:
            output_dir: Directory to save the output files
        """
        self.output_dir = output_dir
        self._ensure_output_dir()
        
        # Get format-specific configurations
        self.json_config = OUTPUT_FORMATS.get('json', {})
        self.csv_config = OUTPUT_FORMATS.get('csv', {})
        self.parquet_config = OUTPUT_FORMATS.get('parquet', {})
    
    def _ensure_output_dir(self) -> None:
        """Create output directory if it doesn't exist."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"Created output directory: {self.output_dir}")
    
    def save_to_json(self, data: List[Dict[str, Any]], filename: str, append: bool = False) -> str:
        """
        Save data to a JSON file.
        
        Args:
            data: List of documents to save
            filename: Name of the output file
            append: Whether to append to an existing file
            
        Returns:
            Path to the saved file
        """
        output_path = os.path.join(self.output_dir, f"{filename}.json")
        mode = 'a' if append else 'w'
        
        try:
            # Convert data to Pandas DataFrame for easy handling
            df = pd.DataFrame(data)
            
            # Handle NaN values before serializing to JSON
            json_str = df.to_json(orient=self.json_config.get('orient', 'records'),
                                 date_format='iso',
                                 indent=self.json_config.get('indent', 2))
            
            with open(output_path, mode, encoding='utf-8') as f:
                f.write(json_str if append else json_str)
            
            logger.info(f"Saved {len(data)} records to JSON file: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to save data to JSON: {str(e)}")
            raise
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str, append: bool = False) -> str:
        """
        Save data to a CSV file.
        
        Args:
            data: List of documents to save
            filename: Name of the output file
            append: Whether to append to an existing file
            
        Returns:
            Path to the saved file
        """
        output_path = os.path.join(self.output_dir, f"{filename}.csv")
        mode = 'a' if append else 'w'
        header = not append
        
        try:
            # Convert data to Pandas DataFrame
            df = pd.DataFrame(data)
            
            # Write to CSV
            df.to_csv(output_path, 
                     mode=mode,
                     header=header,
                     index=False,
                     encoding=self.csv_config.get('encoding', 'utf-8'),
                     quotechar=self.csv_config.get('quotechar', '"'),
                     sep=self.csv_config.get('delimiter', ','))
            
            logger.info(f"Saved {len(data)} records to CSV file: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to save data to CSV: {str(e)}")
            raise
    
    def save_to_parquet(self, data: List[Dict[str, Any]], filename: str) -> str:
        """
        Save data to a Parquet file.
        
        Args:
            data: List of documents to save
            filename: Name of the output file
            
        Returns:
            Path to the saved file
        """
        output_path = os.path.join(self.output_dir, f"{filename}.parquet")
        
        try:
            # Convert data to Pandas DataFrame
            df = pd.DataFrame(data)
            
            # Write to Parquet
            df.to_parquet(output_path,
                         compression=self.parquet_config.get('compression', 'snappy'),
                         row_group_size=self.parquet_config.get('row_group_size', 100000))
            
            logger.info(f"Saved {len(data)} records to Parquet file: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to save data to Parquet: {str(e)}")
            raise
    
    def save_to_multiple_formats(self, data: List[Dict[str, Any]], 
                               filename: str, 
                               formats: List[str]) -> Dict[str, str]:
        """
        Save data to multiple output formats.
        
        Args:
            data: List of documents to save
            filename: Base name of the output file
            formats: List of formats to save ('json', 'csv', 'parquet')
            
        Returns:
            Dictionary mapping format to output path
        """
        results = {}
        
        for fmt in formats:
            if fmt.lower() == 'json':
                path = self.save_to_json(data, filename)
                results['json'] = path
            elif fmt.lower() == 'csv':
                path = self.save_to_csv(data, filename)
                results['csv'] = path
            elif fmt.lower() == 'parquet':
                path = self.save_to_parquet(data, filename)
                results['parquet'] = path
            else:
                logger.warning(f"Unknown format: {fmt}")
        
        return results
    
    def split_and_save(self, data: List[Dict[str, Any]], 
                      filename: str, 
                      format: str, 
                      train_ratio: float = 0.7,
                      val_ratio: float = 0.15,
                      test_ratio: float = 0.15) -> Dict[str, str]:
        """
        Split data into training, validation, and test sets, and save each.
        
        Args:
            data: List of documents to save
            filename: Base name of the output file
            format: Output format ('json', 'csv', 'parquet')
            train_ratio: Proportion of data for training
            val_ratio: Proportion of data for validation
            test_ratio: Proportion of data for testing
            
        Returns:
            Dictionary mapping set name to output path
        """
        # Validate ratios
        total_ratio = train_ratio + val_ratio + test_ratio
        if not 0.999 <= total_ratio <= 1.001:  # Allow for small floating-point errors
            raise ValueError(f"Ratios must sum to 1, but got {total_ratio}")
        
        # Shuffle and split data
        df = pd.DataFrame(data).sample(frac=1, random_state=42).reset_index(drop=True)
        
        n = len(df)
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)
        
        train_data = df[:train_end].to_dict('records')
        val_data = df[train_end:val_end].to_dict('records')
        test_data = df[val_end:].to_dict('records')
        
        logger.info(f"Split data into {len(train_data)} training, {len(val_data)} validation, "
                   f"and {len(test_data)} test samples")
        
        # Save each dataset
        results = {}
        
        if format.lower() == 'json':
            results['train'] = self.save_to_json(train_data, f"{filename}_train")
            results['val'] = self.save_to_json(val_data, f"{filename}_val")
            results['test'] = self.save_to_json(test_data, f"{filename}_test")
        elif format.lower() == 'csv':
            results['train'] = self.save_to_csv(train_data, f"{filename}_train")
            results['val'] = self.save_to_csv(val_data, f"{filename}_val")
            results['test'] = self.save_to_csv(test_data, f"{filename}_test")
        elif format.lower() == 'parquet':
            results['train'] = self.save_to_parquet(train_data, f"{filename}_train")
            results['val'] = self.save_to_parquet(val_data, f"{filename}_val")
            results['test'] = self.save_to_parquet(test_data, f"{filename}_test")
        else:
            logger.warning(f"Unknown format: {format}")
        
        return results

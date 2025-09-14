"""
MongoDB ETL package for machine learning.

Public API re-exports the main ETL class for convenience:

from mongodb_etl import MongoDBETL
"""

from .mongodb_etl import MongoDBETL  # noqa: F401

__all__ = ["MongoDBETL"]
__version__ = "0.1.0"

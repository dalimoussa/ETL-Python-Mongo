"""
Specialized MongoDB extractors for different types of data.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
import logging
import time
from pymongo.cursor import Cursor
from pymongo.errors import OperationFailure

from .. import MongoDBETL
from ..config.config import GEOSPATIAL_CONFIG

logger = logging.getLogger(__name__)

class GeoSpatialExtractor(MongoDBETL):
    """
    Specialized extractor for geospatial data from MongoDB.
    
    This class extends the base MongoDBETL class with specific
    functionality for working with geospatial data and queries.
    """
    
    def __init__(self, collection_name: str, geo_field: str, custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the geospatial extractor.
        
        Args:
            collection_name: Name of the MongoDB collection
            geo_field: Name of the field containing geospatial data
            custom_config: Optional custom configuration to override defaults
        """
        super().__init__(collection_name, custom_config)
        self.geo_field = geo_field
        self._ensure_geo_index()
    
    def _ensure_geo_index(self) -> None:
        """
        Ensure that the appropriate geospatial index exists on the collection.
        Creates a 2dsphere index if it doesn't already exist.
        """
        try:
            # Check if index already exists
            indexes = list(self.collection.list_indexes())
            index_exists = False
            
            for index in indexes:
                if self.geo_field in index['key'] and '2dsphere' in index['key'].values():
                    index_exists = True
                    break
            
            if not index_exists:
                logger.info(f"Creating 2dsphere index on {self.geo_field}")
                self.collection.create_index([(self.geo_field, '2dsphere')])
                logger.info(f"Created 2dsphere index on {self.geo_field}")
        except Exception as e:
            logger.warning(f"Failed to ensure geo index: {str(e)}")
    
    def extract_near(self, 
                    point: Tuple[float, float], 
                    max_distance: Optional[float] = None, 
                    min_distance: Optional[float] = None,
                    limit: Optional[int] = None,
                    additional_filters: Optional[Dict[str, Any]] = None) -> Cursor:
        """
        Extract documents near a specific point using $near operator.
        
        Args:
            point: [longitude, latitude] coordinates
            max_distance: Maximum distance in meters (optional)
            min_distance: Minimum distance in meters (optional)
            limit: Maximum number of results to return
            additional_filters: Additional query filters
            
        Returns:
            MongoDB cursor with the query results
        """
        max_distance = max_distance if max_distance is not None else GEOSPATIAL_CONFIG['default_max_distance'] * 1000
        
        # Build the $near query
        near_query = {
            self.geo_field: {
                '$near': {
                    '$geometry': {
                        'type': 'Point',
                        'coordinates': point
                    }
                }
            }
        }
        
        # Add max/min distance if provided
        if max_distance:
            near_query[self.geo_field]['$near']['$maxDistance'] = max_distance
        
        if min_distance:
            near_query[self.geo_field]['$near']['$minDistance'] = min_distance
        
        # Combine with additional filters
        query = near_query
        if additional_filters:
            query.update(additional_filters)
        
        try:
            cursor = self.collection.find(query)
            
            # Apply limit if provided
            if limit:
                cursor = cursor.limit(limit)
                
            logger.info(f"Executed $near query at coordinates {point} with max distance {max_distance}m")
            return cursor
        except OperationFailure as e:
            logger.error(f"Failed to execute $near query: {str(e)}")
            raise
    
    def extract_within_polygon(self, 
                              polygon_coordinates: List[List[float]], 
                              additional_filters: Optional[Dict[str, Any]] = None) -> Cursor:
        """
        Extract documents within a polygon using $geoWithin operator.
        
        Args:
            polygon_coordinates: List of [longitude, latitude] points forming a polygon
            additional_filters: Additional query filters
            
        Returns:
            MongoDB cursor with the query results
        """
        # Ensure the polygon is closed (first point equals last point)
        if polygon_coordinates[0] != polygon_coordinates[-1]:
            polygon_coordinates.append(polygon_coordinates[0])
        
        # Build the $geoWithin query
        geo_within_query = {
            self.geo_field: {
                '$geoWithin': {
                    '$geometry': {
                        'type': 'Polygon',
                        'coordinates': [polygon_coordinates]
                    }
                }
            }
        }
        
        # Combine with additional filters
        query = geo_within_query
        if additional_filters:
            query.update(additional_filters)
        
        try:
            cursor = self.collection.find(query)
            logger.info(f"Executed $geoWithin polygon query with {len(polygon_coordinates)} points")
            return cursor
        except OperationFailure as e:
            logger.error(f"Failed to execute $geoWithin query: {str(e)}")
            raise
    
    def extract_intersects(self, 
                          geometry: Dict[str, Any], 
                          additional_filters: Optional[Dict[str, Any]] = None) -> Cursor:
        """
        Extract documents that intersect with a GeoJSON geometry using $geoIntersects.
        
        Args:
            geometry: GeoJSON geometry object (Point, LineString, Polygon, etc.)
            additional_filters: Additional query filters
            
        Returns:
            MongoDB cursor with the query results
        """
        # Build the $geoIntersects query
        geo_intersects_query = {
            self.geo_field: {
                '$geoIntersects': {
                    '$geometry': geometry
                }
            }
        }
        
        # Combine with additional filters
        query = geo_intersects_query
        if additional_filters:
            query.update(additional_filters)
        
        try:
            cursor = self.collection.find(query)
            logger.info(f"Executed $geoIntersects query with geometry type {geometry.get('type')}")
            return cursor
        except OperationFailure as e:
            logger.error(f"Failed to execute $geoIntersects query: {str(e)}")
            raise
    
    def aggregate_by_proximity(self, 
                              point: Tuple[float, float],
                              max_distance: float,
                              group_by_field: str,
                              agg_pipeline: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Aggregate documents by proximity to a point using geospatial pipeline.
        
        Args:
            point: [longitude, latitude] coordinates
            max_distance: Maximum distance in meters
            group_by_field: Field to group by in the aggregation
            agg_pipeline: Additional aggregation pipeline stages
            
        Returns:
            List of aggregated results
        """
        # Start with $geoNear stage
        pipeline = [
            {
                '$geoNear': {
                    'near': {
                        'type': 'Point',
                        'coordinates': point
                    },
                    'distanceField': 'distance',
                    'maxDistance': max_distance,
                    'spherical': True
                }
            },
            {
                '$group': {
                    '_id': f'${group_by_field}',
                    'count': {'$sum': 1},
                    'avg_distance': {'$avg': '$distance'},
                    'documents': {'$push': '$$ROOT'}
                }
            },
            {
                '$sort': {'avg_distance': 1}
            }
        ]
        
        # Append any additional pipeline stages
        if agg_pipeline:
            pipeline.extend(agg_pipeline)
        
        try:
            start_time = time.time()
            results = list(self.collection.aggregate(pipeline))
            logger.info(f"Executed geospatial aggregation in {time.time() - start_time:.2f}s")
            return results
        except Exception as e:
            logger.error(f"Failed to execute geospatial aggregation: {str(e)}")
            raise

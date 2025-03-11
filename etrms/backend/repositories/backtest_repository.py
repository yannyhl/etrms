"""
Repository for backtesting operations.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from etrms.backend.db.database import get_db
from etrms.backend.models.backtest import (
    BacktestConfig,
    BacktestCreate,
    BacktestUpdate,
    BacktestResult,
    BacktestStatus,
    BacktestResponse
)
from etrms.backend.utils.error_handler import NotFoundException, ConflictException

class BacktestRepository:
    """Repository for backtest database operations"""
    
    def __init__(self, db=None):
        self.db = db or get_db()
        self.config_collection = self.db["backtest_configs"]
        self.result_collection = self.db["backtest_results"]
    
    def get_config_by_id(self, config_id: str) -> Optional[BacktestConfig]:
        """Get a backtest configuration by ID"""
        config_data = self.config_collection.find_one({"_id": config_id})
        if config_data:
            return self._map_to_config(config_data)
        return None
    
    def get_result_by_id(self, result_id: str) -> Optional[BacktestResult]:
        """Get a backtest result by ID"""
        result_data = self.result_collection.find_one({"_id": result_id})
        if result_data:
            return self._map_to_result(result_data)
        return None
    
    def get_result_by_config_id(self, config_id: str) -> Optional[BacktestResult]:
        """Get a backtest result by config ID"""
        result_data = self.result_collection.find_one({"config_id": config_id})
        if result_data:
            return self._map_to_result(result_data)
        return None
    
    def get_all_configs(self, skip: int = 0, limit: int = 100) -> List[BacktestConfig]:
        """Get all backtest configurations with pagination"""
        config_data = list(self.config_collection.find().skip(skip).limit(limit))
        return [self._map_to_config(config) for config in config_data]
    
    def count_configs(self) -> int:
        """Count all backtest configurations"""
        return self.config_collection.count_documents({})
    
    def create_config(self, backtest_create: BacktestCreate) -> BacktestConfig:
        """Create a new backtest configuration"""
        # Check if a backtest with the same name already exists
        existing = self.config_collection.find_one({"name": backtest_create.name})
        if existing:
            raise ConflictException(f"Backtest with name '{backtest_create.name}' already exists")
        
        now = datetime.utcnow()
        config_id = str(uuid.uuid4())
        
        config_data = backtest_create.dict()
        config_data["_id"] = config_id
        config_data["created_at"] = now
        config_data["updated_at"] = now
        
        self.config_collection.insert_one(config_data)
        
        # Create a pending result
        result_id = str(uuid.uuid4())
        result_data = {
            "_id": result_id,
            "config_id": config_id,
            "status": BacktestStatus.PENDING.value,
            "created_at": now,
            "updated_at": now
        }
        
        self.result_collection.insert_one(result_data)
        
        return self._map_to_config(config_data)
    
    def update_config(self, config_id: str, backtest_update: BacktestUpdate) -> BacktestConfig:
        """Update a backtest configuration"""
        # Check if the backtest exists
        config = self.get_config_by_id(config_id)
        if not config:
            raise NotFoundException(f"Backtest with ID '{config_id}' not found")
        
        # Check if the name is being changed and if it conflicts with an existing backtest
        if backtest_update.name and backtest_update.name != config.name:
            existing = self.config_collection.find_one({
                "name": backtest_update.name,
                "_id": {"$ne": config_id}
            })
            if existing:
                raise ConflictException(f"Backtest with name '{backtest_update.name}' already exists")
        
        update_data = backtest_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        result = self.config_collection.update_one(
            {"_id": config_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise NotFoundException(f"Backtest with ID '{config_id}' not found")
        
        return self.get_config_by_id(config_id)
    
    def delete_config(self, config_id: str) -> None:
        """Delete a backtest configuration and its results"""
        # Check if the backtest exists
        config = self.get_config_by_id(config_id)
        if not config:
            raise NotFoundException(f"Backtest with ID '{config_id}' not found")
        
        # Delete the configuration
        result = self.config_collection.delete_one({"_id": config_id})
        if result.deleted_count == 0:
            raise NotFoundException(f"Backtest with ID '{config_id}' not found")
        
        # Delete the results
        self.result_collection.delete_many({"config_id": config_id})
    
    def update_result(self, config_id: str, status: BacktestStatus, data: Dict[str, Any] = None) -> BacktestResult:
        """Update a backtest result"""
        # Check if the backtest exists
        config = self.get_config_by_id(config_id)
        if not config:
            raise NotFoundException(f"Backtest with ID '{config_id}' not found")
        
        # Get the result
        result = self.get_result_by_config_id(config_id)
        if not result:
            raise NotFoundException(f"Result for backtest with ID '{config_id}' not found")
        
        update_data = {
            "status": status.value,
            "updated_at": datetime.utcnow()
        }
        
        if data:
            update_data.update(data)
        
        result = self.result_collection.update_one(
            {"config_id": config_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise NotFoundException(f"Result for backtest with ID '{config_id}' not found")
        
        return self.get_result_by_config_id(config_id)
    
    def get_backtest_response(self, config_id: str) -> BacktestResponse:
        """Get a complete backtest response including config and result"""
        # Get the config
        config = self.get_config_by_id(config_id)
        if not config:
            raise NotFoundException(f"Backtest with ID '{config_id}' not found")
        
        # Get the result
        result = self.get_result_by_config_id(config_id)
        if not result:
            raise NotFoundException(f"Result for backtest with ID '{config_id}' not found")
        
        # Create the response
        return BacktestResponse(
            id=config_id,
            name=config.name,
            description=config.description,
            type=config.type,
            start_date=config.start_date,
            end_date=config.end_date,
            exchanges=config.exchanges,
            symbols=config.symbols,
            timeframe=config.timeframe,
            initial_capital=config.initial_capital,
            circuit_breakers=config.circuit_breakers,
            parameters=config.parameters,
            status=result.status,
            created_at=config.created_at,
            updated_at=config.updated_at,
            result=result
        )
    
    def get_all_backtest_responses(self, skip: int = 0, limit: int = 100) -> List[BacktestResponse]:
        """Get all backtest responses with pagination"""
        configs = self.get_all_configs(skip, limit)
        responses = []
        
        for config in configs:
            try:
                response = self.get_backtest_response(config.id)
                responses.append(response)
            except NotFoundException:
                # Skip backtests with missing results
                continue
        
        return responses
    
    def _map_to_config(self, config_data: Dict[str, Any]) -> BacktestConfig:
        """Map database config data to BacktestConfig model"""
        config_data = dict(config_data)
        config_data["id"] = config_data.pop("_id")
        return BacktestConfig(**config_data)
    
    def _map_to_result(self, result_data: Dict[str, Any]) -> BacktestResult:
        """Map database result data to BacktestResult model"""
        result_data = dict(result_data)
        result_data["id"] = result_data.pop("_id")
        return BacktestResult(**result_data) 
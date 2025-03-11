from typing import Optional, Dict, Any
from datetime import datetime
import uuid
from etrms.backend.models.user import User, UserCreate, UserUpdate
from etrms.backend.db.database import get_db
from etrms.backend.utils.error_handler import NotFoundException, ConflictException

class UserRepository:
    """Repository for user database operations"""
    
    def __init__(self, db=None):
        self.db = db or get_db()
        self.collection = self.db["users"]
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        user_data = self.collection.find_one({"_id": user_id})
        if user_data:
            return self._map_to_user(user_data)
        return None
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get a user by username"""
        user_data = self.collection.find_one({"username": username})
        if user_data:
            return self._map_to_user(user_data)
        return None
    
    def create(self, user_create: UserCreate, hashed_password: str) -> User:
        """Create a new user"""
        # Check if username already exists
        if self.get_by_username(user_create.username):
            raise ConflictException(f"Username '{user_create.username}' already exists")
        
        now = datetime.utcnow()
        user_id = str(uuid.uuid4())
        
        user_data = {
            "_id": user_id,
            "username": user_create.username,
            "email": user_create.email,
            "hashed_password": hashed_password,
            "is_active": user_create.is_active,
            "theme": user_create.theme,
            "default_exchange": user_create.default_exchange,
            "default_timeframe": user_create.default_timeframe,
            "created_at": now,
            "updated_at": now
        }
        
        self.collection.insert_one(user_data)
        return self._map_to_user(user_data)
    
    def update(self, user_id: str, user_update: UserUpdate) -> User:
        """Update a user's profile"""
        # Check if user exists
        user = self.get_by_id(user_id)
        if not user:
            raise NotFoundException(f"User with ID '{user_id}' not found")
        
        update_data = user_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        result = self.collection.update_one(
            {"_id": user_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise NotFoundException(f"User with ID '{user_id}' not found")
        
        return self.get_by_id(user_id)
    
    def update_password(self, user_id: str, hashed_password: str) -> None:
        """Update a user's password"""
        # Check if user exists
        user = self.get_by_id(user_id)
        if not user:
            raise NotFoundException(f"User with ID '{user_id}' not found")
        
        result = self.collection.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "hashed_password": hashed_password,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise NotFoundException(f"User with ID '{user_id}' not found")
    
    def _map_to_user(self, user_data: Dict[str, Any]) -> User:
        """Map database user data to User model"""
        return User(
            id=user_data["_id"],
            username=user_data["username"],
            email=user_data.get("email"),
            is_active=user_data.get("is_active", True),
            theme=user_data.get("theme", "dark"),
            default_exchange=user_data.get("default_exchange"),
            default_timeframe=user_data.get("default_timeframe", "1h"),
            created_at=user_data["created_at"],
            updated_at=user_data["updated_at"]
        ) 
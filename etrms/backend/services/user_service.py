from typing import Optional
from passlib.context import CryptContext
from etrms.backend.models.user import User, UserCreate, UserUpdate
from etrms.backend.repositories.user_repository import UserRepository
from etrms.backend.utils.error_handler import UnauthorizedException, NotFoundException

class UserService:
    """Service for handling user operations"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def get_user_by_id(self, user_id: str) -> User:
        """Get a user by ID"""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundException(f"User with ID '{user_id}' not found")
        return user
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username"""
        return self.user_repository.get_by_username(username)
    
    def authenticate_user(self, username: str, password: str) -> User:
        """Authenticate a user with username and password"""
        user = self.get_user_by_username(username)
        if not user:
            raise UnauthorizedException("Invalid username or password")
        
        if not self.verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid username or password")
        
        return user
    
    def create_user(self, user_create: UserCreate, hashed_password: str) -> User:
        """Create a new user"""
        return self.user_repository.create(user_create, hashed_password)
    
    def update_user(self, user_id: str, user_update: UserUpdate) -> User:
        """Update a user's profile"""
        return self.user_repository.update(user_id, user_update)
    
    def update_password(self, user_id: str, hashed_password: str) -> None:
        """Update a user's password"""
        self.user_repository.update_password(user_id, hashed_password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password) 
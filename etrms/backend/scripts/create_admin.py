#!/usr/bin/env python
"""
Create Admin User Script

This script creates an admin user for the ETRMS system.
"""
import os
import sys
import argparse
from datetime import datetime

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError

# Load environment variables
load_dotenv()

from data.database import SessionLocal, init_db
from data.models.users import User
from api.services.auth import get_password_hash, get_user_by_username, get_user_by_email
from utils.logger import get_logger

# Create a logger instance
logger = get_logger(__name__)


def create_admin_user(username: str, email: str, password: str) -> None:
    """
    Create an admin user.
    
    Args:
        username: The username for the admin user.
        email: The email for the admin user.
        password: The password for the admin user.
    """
    # Initialize the database
    init_db()
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = get_user_by_username(db, username)
        if existing_user:
            logger.warning(f"User with username '{username}' already exists")
            return
        
        existing_user = get_user_by_email(db, email)
        if existing_user:
            logger.warning(f"User with email '{email}' already exists")
            return
        
        # Create the admin user
        hashed_password = get_password_hash(password)
        admin_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=True,
            role="admin",
            created_at=datetime.utcnow(),
        )
        
        # Add to database
        db.add(admin_user)
        db.commit()
        
        logger.info(f"Admin user '{username}' created successfully")
    except IntegrityError:
        db.rollback()
        logger.error("Error creating admin user: username or email already exists")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating admin user: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create an admin user for the ETRMS system")
    parser.add_argument("--username", required=True, help="Username for the admin user")
    parser.add_argument("--email", required=True, help="Email for the admin user")
    parser.add_argument("--password", required=True, help="Password for the admin user")
    
    args = parser.parse_args()
    
    create_admin_user(args.username, args.email, args.password) 
# Authentication System Documentation

## Overview

The Enhanced Trading Risk Management System (ETRMS) implements a comprehensive authentication system to secure access to the application. This document outlines the authentication architecture, components, and usage guidelines.

## Architecture

The authentication system follows a token-based approach using JSON Web Tokens (JWT):

1. **User Authentication**: Users provide credentials (username/email and password) to authenticate.
2. **Token Generation**: Upon successful authentication, the server generates a JWT token.
3. **Token Validation**: Subsequent requests include the token in the Authorization header for validation.
4. **Protected Routes**: API endpoints and frontend routes are protected to ensure only authenticated users can access them.

## Backend Components

### User Model (`data/models/users.py`)

The User model defines the database schema for storing user information:

- `id`: Primary key
- `username`: Unique username
- `email`: Unique email address
- `hashed_password`: Securely hashed password
- `is_active`: Boolean indicating if the account is active
- `is_superuser`: Boolean indicating superuser privileges
- `role`: User's role (default is "user")
- `created_at`: Timestamp for when the user was created
- `last_login`: Timestamp for the user's last login

### Authentication Schemas (`api/schemas/auth.py`)

Pydantic schemas for request and response validation:

- `Token`: JWT access token and type
- `TokenData`: Decoded JWT content
- `UserBase`: Base user attributes
- `UserCreate`: User registration data
- `UserLogin`: Login credentials
- `UserResponse`: User profile response
- `UserUpdate`: Profile update data
- `PasswordReset`: Password reset data

### Authentication Service (`api/services/auth.py`)

Core authentication functionality:

- Password hashing and verification
- JWT token generation and validation
- User retrieval and authentication
- Dependency functions for protected routes

### Authentication Controller (`api/controllers/auth.py`)

Business logic for authentication operations:

- User registration
- Profile management
- User listing and deactivation

### Authentication Routes (`api/routes/auth.py`)

API endpoints for authentication:

- `POST /auth/register`: Create a new user
- `POST /auth/login`: Authenticate and get a token
- `GET /auth/me`: Get current user profile
- `PUT /auth/me`: Update current user profile
- `GET /auth/users`: List all users (admin only)
- `GET /auth/users/{user_id}`: Get a specific user
- `PUT /auth/users/{user_id}`: Update a specific user
- `DELETE /auth/users/{user_id}`: Deactivate a user (admin only)

### Authentication Middleware (`api/middleware/auth.py`)

HTTP middleware for token validation:

- Extracts and validates JWT tokens
- Adds user information to request state
- Handles authentication errors
- Defines public paths that don't require authentication

## Frontend Components

### Authentication Service (`services/authService.js`)

Client-side authentication functionality:

- Token storage and retrieval
- API calls for login, registration, and profile management
- Axios interceptors for adding authentication headers

### Protected Route Component (`components/ProtectedRoute.js`)

React component that protects routes requiring authentication:

- Verifies authentication status
- Redirects to login if not authenticated
- Shows loading state during verification

### Authentication Pages

- `Login.js`: User login form
- `Register.js`: User registration form
- `Profile.js`: User profile management

## Usage Guidelines

### Creating an Admin User

Use the provided script to create an admin user:

```bash
python -m etrms.backend.scripts.create_admin --username admin --email admin@example.com --password securepassword
```

### Securing API Endpoints

To secure an API endpoint, use the appropriate dependency:

```python
@router.get("/protected-endpoint")
async def protected_endpoint(current_user: User = Depends(get_current_active_user)):
    # Only accessible to authenticated users
    return {"message": "This is protected", "user": current_user.username}
```

For admin-only endpoints:

```python
@router.get("/admin-endpoint")
async def admin_endpoint(current_user: User = Depends(get_current_admin_user)):
    # Only accessible to admin users
    return {"message": "This is admin-only"}
```

### Frontend Authentication

To access the authentication state in React components:

```javascript
import authService from '../services/authService';

// Check if user is authenticated
const isLoggedIn = authService.isAuthenticated();

// Get current user
const currentUser = authService.getUser();

// Logout
const handleLogout = () => {
  authService.logout();
};
```

## Security Considerations

1. **Password Storage**: Passwords are hashed using bcrypt before storage.
2. **Token Expiration**: JWTs have a configurable expiration time.
3. **HTTPS**: All production deployments should use HTTPS.
4. **CORS**: Cross-Origin Resource Sharing is configured to restrict access.
5. **Rate Limiting**: Consider implementing rate limiting for login attempts.

## Future Enhancements

1. **Two-Factor Authentication**: Add 2FA for additional security.
2. **OAuth Integration**: Support for third-party authentication providers.
3. **Password Reset**: Implement a password reset flow via email.
4. **Session Management**: Allow users to view and terminate active sessions.
5. **Role-Based Access Control**: Enhance the role system for more granular permissions. 
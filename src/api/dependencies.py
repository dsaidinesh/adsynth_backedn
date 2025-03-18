"""Dependencies for FastAPI application.
Provides Supabase client and authentication dependencies.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from postgrest.exceptions import APIError
import jwt

from src.database.supabase_config import get_supabase_client
from supabase import Client

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

def get_supabase() -> Client:
    """Get Supabase client."""
    return get_supabase_client()

# Update the import statement
from jwt import PyJWT

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    supabase: Client = Depends(get_supabase)
) -> dict:
    """Get current authenticated user from Supabase JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Create a PyJWT instance
        jwt_instance = PyJWT()
        
        try:
            # Decode token without verification to get user info
            decoded = jwt_instance.decode(token, options={"verify_signature": False})
            user_id = decoded.get('sub')
            
            if not user_id:
                raise credentials_exception
            
            try:
                # Get current session
                session = supabase.auth.get_session()
                
                # Validate session exists and has refresh token
                if not session or not session.refresh_token:
                    raise credentials_exception
                
                # Set session with current tokens
                supabase.auth.set_session(token, session.refresh_token)
                
                # Return user data from valid token
                return {
                    "id": user_id,
                    "email": decoded.get('email'),
                    "username": decoded.get('username'),
                    "access_token": token,
                    "refresh_token": session.refresh_token
                }
                
            except APIError as api_error:
                if 'JWT expired' in str(api_error):
                    # Handle expired token
                    session = supabase.auth.get_session()
                    if not session or not session.refresh_token:
                        raise credentials_exception
                    
                    # Attempt to refresh the session
                    try:
                        refresh_response = supabase.auth.refresh_session(session.refresh_token)
                        
                        if not refresh_response or not refresh_response.session:
                            raise credentials_exception
                        
                        # Get new tokens
                        new_token = refresh_response.session.access_token
                        new_refresh_token = refresh_response.session.refresh_token
                        
                        # Update session with new tokens
                        supabase.auth.set_session(new_token, new_refresh_token)
                        
                        # Decode new token
                        decoded = jwt_instance.decode(new_token, options={"verify_signature": False})
                        user_id = decoded.get('sub')
                        
                        # Return updated user data
                        return {
                            "id": user_id,
                            "email": decoded.get('email'),
                            "username": decoded.get('username'),
                            "access_token": new_token,
                            "refresh_token": new_refresh_token
                        }
                        
                    except Exception as refresh_error:
                        print(f"Token refresh error: {str(refresh_error)}")
                        raise credentials_exception
                else:
                    raise api_error
                    
        except jwt.InvalidTokenError:
            raise credentials_exception
            
    except Exception as e:
        print(f"Token validation error: {str(e)}")
        raise credentials_exception
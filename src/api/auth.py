"""Authentication router and dependencies for FastAPI application.
Provides Supabase authentication integration and JWT verification.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Body
from supabase import Client, create_client
from typing import Optional
import os

from src.database.supabase_config import get_supabase_client

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

# Initialize Supabase client
supabase: Client = get_supabase_client()

def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token from request header."""
    token = credentials.credentials
    try:
        # Verify token with Supabase
        user = supabase.auth.get_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post("/refresh-token")
async def refresh_token(refresh_token: str = Body(..., embed=True)):
    """Refresh an expired JWT token."""
    try:
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Refresh token is required"
            )
            
        # Refresh the session using the provided refresh token
        refresh_response = supabase.auth.refresh_session({
            "refresh_token": refresh_token
        })
        
        if not refresh_response or not refresh_response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to refresh token"
            )
            
        return {
            "access_token": refresh_response.session.access_token,
            "refresh_token": refresh_response.session.refresh_token
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.get("/user")
async def get_user(user = Depends(verify_jwt)):
    """Get current authenticated user info."""
    return {
        "id": user.user.id,
        "email": user.user.email,
        "last_sign_in_at": user.user.last_sign_in_at
    }
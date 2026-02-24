from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..models.database import get_db
from ..models.schemas import User
from ..config import settings

security = HTTPBearer()


class AuthService:
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm

    def create_access_token(self, email: str, expires_delta: Optional[timedelta] = None):
        """Create JWT access token for user"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        
        to_encode = {"sub": email, "exp": expire}
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> str:
        """Verify JWT token and return email"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            email: str = payload.get("sub")
            if email is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            return email
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

    async def get_current_user_email(self, credentials: HTTPAuthorizationCredentials = Depends(security)):
        """FastAPI dependency to get current user email from token"""
        token = credentials.credentials
        email = self.verify_token(token)
        return email

    async def get_or_create_user(self, email: str) -> User:
        """Get existing user or create new one"""
        db = get_db()
        
        # Check if user exists
        result = db.table("users").select("*").eq("email", email).execute()
        
        if result.data:
            return User(**result.data[0])
        
        # Create new user
        user_data = {"email": email}
        result = db.table("users").insert(user_data).execute()
        
        if result.data:
            return User(**result.data[0])
        
        raise HTTPException(status_code=500, detail="Failed to create user")


auth_service = AuthService()
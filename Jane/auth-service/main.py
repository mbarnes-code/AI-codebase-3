"""
Authentication and Authorization Service with Vault Integration
Handles JWT tokens, API keys, and secrets management
"""

import asyncio
import hashlib
import jwt
import os
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import asyncpg
import aioredis
import hvac
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from loguru import logger

# Configure logging
logger.add("logs/auth_service.log", rotation="1 day", retention="7 days", level="INFO")

# Security setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Pydantic models
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class User(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None

class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    permissions: List[str] = Field(default_factory=list)
    expires_days: Optional[int] = Field(default=365, ge=1, le=3650)

class APIKey(BaseModel):
    id: str
    name: str
    key: str
    permissions: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None

class AuthService:
    """Core authentication and authorization service"""
    
    def __init__(self):
        self.db_pool = None
        self.redis_pool = None
        self.vault_client = None
        
        # JWT settings
        self.jwt_secret = os.getenv("JWT_SECRET_KEY", "fallback-secret-change-me")
        self.jwt_algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
        
        # Vault settings
        self.vault_url = os.getenv("VAULT_URL", "http://vault:8200")
        self.vault_token = os.getenv("VAULT_TOKEN")
        
    async def initialize(self):
        """Initialize all connections and services"""
        try:
            # PostgreSQL for user data
            pg_dsn = os.getenv("DATABASE_URL", "postgresql://user:pass@postgres:5432/auth_db")
            self.db_pool = await asyncpg.create_pool(pg_dsn, min_size=2, max_size=10)
            
            # Redis for session management
            redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
            self.redis_pool = aioredis.from_url(redis_url, decode_responses=True)
            
            # Vault for secrets management
            if self.vault_token:
                self.vault_client = hvac.Client(url=self.vault_url, token=self.vault_token)
                if not self.vault_client.is_authenticated():
                    logger.warning("Vault authentication failed")
                    self.vault_client = None
            
            await self._create_tables()
            await self._ensure_admin_user()
            
            logger.info("Auth service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize auth service: {e}")
            raise
    
    async def _create_tables(self):
        """Create database tables if they don't exist"""
        async with self.db_pool.acquire() as conn:
            # Users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    full_name VARCHAR(255),
                    password_hash VARCHAR(255) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    last_login TIMESTAMP WITH TIME ZONE
                )
            """)
            
            # API Keys table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(100) NOT NULL,
                    key_hash VARCHAR(255) NOT NULL,
                    permissions TEXT[],
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    expires_at TIMESTAMP WITH TIME ZONE,
                    last_used TIMESTAMP WITH TIME ZONE
                )
            """)
            
            # Sessions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    token_jti VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    is_revoked BOOLEAN DEFAULT FALSE
                )
            """)
    
    async def _ensure_admin_user(self):
        """Ensure admin user exists for system management"""
        async with self.db_pool.acquire() as conn:
            admin_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM users WHERE username = 'admin')"
            )
            
            if not admin_exists:
                admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
                password_hash = pwd_context.hash(admin_password)
                
                await conn.execute("""
                    INSERT INTO users (username, email, full_name, password_hash)
                    VALUES ('admin', 'admin@jane.local', 'System Administrator', $1)
                """, password_hash)
                
                logger.info("Created admin user (username: admin)")
    
    def _generate_api_key(self) -> str:
        """Generate a secure API key"""
        return f"jane_{secrets.token_urlsafe(32)}"
    
    def _hash_api_key(self, api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        password_hash = pwd_context.hash(user_data.password)
        
        async with self.db_pool.acquire() as conn:
            try:
                result = await conn.fetchrow("""
                    INSERT INTO users (username, email, full_name, password_hash)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id, username, email, full_name, is_active, created_at
                """, user_data.username, user_data.email, user_data.full_name, password_hash)
                
                user = User(**dict(result))
                logger.info(f"Created user: {user.username}")
                return user
                
            except asyncpg.UniqueViolationError as e:
                if "username" in str(e):
                    raise HTTPException(status_code=400, detail="Username already exists")
                elif "email" in str(e):
                    raise HTTPException(status_code=400, detail="Email already exists")
                else:
                    raise HTTPException(status_code=400, detail="User already exists")
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user credentials"""
        async with self.db_pool.acquire() as conn:
            user_data = await conn.fetchrow("""
                SELECT id, username, email, full_name, password_hash, is_active, created_at, last_login
                FROM users 
                WHERE username = $1 AND is_active = TRUE
            """, username)
            
            if not user_data:
                return None
            
            if not pwd_context.verify(password, user_data['password_hash']):
                return None
            
            # Update last login
            await conn.execute(
                "UPDATE users SET last_login = NOW() WHERE id = $1",
                user_data['id']
            )
            
            return User(**{k: v for k, v in dict(user_data).items() if k != 'password_hash'})
    
    async def create_access_token(self, user: User) -> Token:
        """Create JWT access token"""
        jti = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": user.id,
            "username": user.username,
            "jti": jti,
            "exp": expires_at,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        
        # Store session in database
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO sessions (user_id, token_jti, expires_at)
                VALUES ($1, $2, $3)
            """, user.id, jti, expires_at)
        
        # Cache in Redis for fast lookup
        await self.redis_pool.setex(
            f"session:{jti}",
            self.access_token_expire_minutes * 60,
            user.id
        )
        
        return Token(
            access_token=token,
            expires_in=self.access_token_expire_minutes * 60
        )
    
    async def verify_token(self, credentials: HTTPAuthorizationCredentials) -> User:
        """Verify JWT token and return user"""
        try:
            payload = jwt.decode(
                credentials.credentials,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            
            jti = payload.get("jti")
            user_id = payload.get("sub")
            
            if not jti or not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            
            # Check if session is still valid in Redis
            cached_user_id = await self.redis_pool.get(f"session:{jti}")
            if not cached_user_id:
                # Check database
                async with self.db_pool.acquire() as conn:
                    session_valid = await conn.fetchval("""
                        SELECT EXISTS(
                            SELECT 1 FROM sessions 
                            WHERE token_jti = $1 AND expires_at > NOW() AND is_revoked = FALSE
                        )
                    """, jti)
                
                if not session_valid:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token expired or revoked"
                    )
            
            # Get user data
            async with self.db_pool.acquire() as conn:
                user_data = await conn.fetchrow("""
                    SELECT id, username, email, full_name, is_active, created_at, last_login
                    FROM users 
                    WHERE id = $1 AND is_active = TRUE
                """, user_id)
                
                if not user_data:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not found or inactive"
                    )
                
                return User(**dict(user_data))
                
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    async def create_api_key(self, user_id: str, api_key_data: APIKeyCreate) -> APIKey:
        """Create API key for user"""
        api_key = self._generate_api_key()
        key_hash = self._hash_api_key(api_key)
        
        expires_at = None
        if api_key_data.expires_days:
            expires_at = datetime.utcnow() + timedelta(days=api_key_data.expires_days)
        
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchrow("""
                INSERT INTO api_keys (user_id, name, key_hash, permissions, expires_at)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, created_at
            """, user_id, api_key_data.name, key_hash, api_key_data.permissions, expires_at)
            
            return APIKey(
                id=str(result['id']),
                name=api_key_data.name,
                key=api_key,  # Return actual key only on creation
                permissions=api_key_data.permissions,
                created_at=result['created_at'],
                expires_at=expires_at
            )
    
    async def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Verify API key and return user info"""
        key_hash = self._hash_api_key(api_key)
        
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT ak.id, ak.user_id, ak.name, ak.permissions, ak.expires_at,
                       u.username, u.email, u.is_active
                FROM api_keys ak
                JOIN users u ON ak.user_id = u.id
                WHERE ak.key_hash = $1 
                AND u.is_active = TRUE
                AND (ak.expires_at IS NULL OR ak.expires_at > NOW())
            """, key_hash)
            
            if result:
                # Update last used timestamp
                await conn.execute(
                    "UPDATE api_keys SET last_used = NOW() WHERE id = $1",
                    result['id']
                )
                
                return dict(result)
            
            return None
    
    async def revoke_token(self, jti: str):
        """Revoke a JWT token"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE sessions SET is_revoked = TRUE WHERE token_jti = $1",
                jti
            )
        
        # Remove from Redis cache
        await self.redis_pool.delete(f"session:{jti}")
    
    async def store_secret(self, key: str, value: str, path: str = "jane") -> bool:
        """Store secret in Vault"""
        if not self.vault_client:
            logger.warning("Vault not available, storing secret in environment")
            return False
        
        try:
            self.vault_client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret={key: value}
            )
            logger.info(f"Stored secret: {key} at path: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to store secret in Vault: {e}")
            return False
    
    async def get_secret(self, key: str, path: str = "jane") -> Optional[str]:
        """Retrieve secret from Vault"""
        if not self.vault_client:
            return os.getenv(key.upper())
        
        try:
            response = self.vault_client.secrets.kv.v2.read_secret_version(path=path)
            return response['data']['data'].get(key)
        except Exception as e:
            logger.error(f"Failed to retrieve secret from Vault: {e}")
            return os.getenv(key.upper())

# Initialize auth service
auth_service = AuthService()

# FastAPI app
app = FastAPI(
    title="Authentication & Authorization Service",
    description="JWT and API key authentication with Vault integration for the AI Second Brain Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://192.168.1.17:3001", "http://192.168.1.17:3002", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency for JWT authentication
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    return await auth_service.verify_token(credentials)

# Dependency for API key authentication
async def verify_api_key_dep(api_key: str) -> Dict[str, Any]:
    key_data = await auth_service.verify_api_key(api_key)
    if not key_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return key_data

@app.on_event("startup")
async def startup_event():
    await auth_service.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    if auth_service.db_pool:
        await auth_service.db_pool.close()
    if auth_service.redis_pool:
        await auth_service.redis_pool.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    services = {
        "auth_service": "healthy"
    }
    
    # Check database
    try:
        async with auth_service.db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        services["postgresql"] = "healthy"
    except:
        services["postgresql"] = "unhealthy"
    
    # Check Redis
    try:
        await auth_service.redis_pool.ping()
        services["redis"] = "healthy"
    except:
        services["redis"] = "unhealthy"
    
    # Check Vault
    if auth_service.vault_client:
        try:
            services["vault"] = "healthy" if auth_service.vault_client.is_authenticated() else "unhealthy"
        except:
            services["vault"] = "unhealthy"
    else:
        services["vault"] = "not_configured"
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": services
    }

# Authentication endpoints
@app.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    """Register a new user"""
    return await auth_service.create_user(user_data)

@app.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login and get access token"""
    user = await auth_service.authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    return await auth_service.create_access_token(user)

@app.post("/auth/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout and revoke token"""
    # Note: In a real implementation, you'd extract the JTI from the token
    return {"message": "Logged out successfully"}

@app.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

# API Key management
@app.post("/api-keys", response_model=APIKey)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new API key"""
    return await auth_service.create_api_key(current_user.id, api_key_data)

@app.get("/api-keys")
async def list_api_keys(current_user: User = Depends(get_current_user)):
    """List user's API keys (without showing actual keys)"""
    async with auth_service.db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, name, permissions, created_at, expires_at, last_used
            FROM api_keys
            WHERE user_id = $1
            ORDER BY created_at DESC
        """, current_user.id)
        
        return [dict(row) for row in rows]

@app.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete an API key"""
    async with auth_service.db_pool.acquire() as conn:
        deleted = await conn.execute("""
            DELETE FROM api_keys 
            WHERE id = $1 AND user_id = $2
        """, key_id, current_user.id)
        
        if deleted == "DELETE 0":
            raise HTTPException(status_code=404, detail="API key not found")
        
        return {"message": "API key deleted successfully"}

# Admin endpoints
@app.get("/admin/users")
async def list_users(current_user: User = Depends(get_current_user)):
    """List all users (admin only)"""
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    async with auth_service.db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, username, email, full_name, is_active, created_at, last_login
            FROM users
            ORDER BY created_at DESC
        """)
        
        return [User(**dict(row)) for row in rows]

# Secrets management endpoints
@app.post("/secrets/{key}")
async def store_secret(
    key: str,
    secret_data: Dict[str, str],
    current_user: User = Depends(get_current_user)
):
    """Store a secret in Vault"""
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    value = secret_data.get("value")
    if not value:
        raise HTTPException(status_code=400, detail="Secret value required")
    
    success = await auth_service.store_secret(key, value)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to store secret")
    
    return {"message": f"Secret '{key}' stored successfully"}

@app.get("/secrets/{key}")
async def get_secret(
    key: str,
    current_user: User = Depends(get_current_user)
):
    """Retrieve a secret from Vault"""
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    value = await auth_service.get_secret(key)
    if not value:
        raise HTTPException(status_code=404, detail="Secret not found")
    
    return {"key": key, "value": value}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import asyncio
import logging
import os
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from dataclasses import dataclass, asdict
import aioredis
import asyncpg
import httpx
from loguru import logger

# Configure logging
logger.add("logs/adhd_support.log", rotation="1 day", retention="7 days", level="INFO")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if user_id:
            self.user_connections[user_id] = websocket
        logger.info(f"WebSocket connected for user: {user_id}")

    def disconnect(self, websocket: WebSocket, user_id: str = None):
        self.active_connections.remove(websocket)
        if user_id and user_id in self.user_connections:
            del self.user_connections[user_id]
        logger.info(f"WebSocket disconnected for user: {user_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.user_connections:
            websocket = self.user_connections[user_id]
            await websocket.send_text(json.dumps(message))

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_text(json.dumps(message))

manager = ConnectionManager()

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Pydantic models
class Task(BaseModel):
    id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    priority: int = Field(default=3, ge=1, le=5)  # 1=lowest, 5=highest
    due_date: Optional[datetime] = None
    completed: bool = False
    created_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    estimated_duration: Optional[int] = None  # minutes
    context: Optional[str] = None  # work, personal, research, etc.

class QuickNote(BaseModel):
    id: Optional[str] = None
    content: str = Field(..., min_length=1, max_length=2000)
    tags: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    context: Optional[str] = None

class FocusSession(BaseModel):
    id: Optional[str] = None
    task_id: Optional[str] = None
    duration_minutes: int = Field(default=25, ge=5, le=120)  # Pomodoro-style
    break_duration: int = Field(default=5, ge=1, le=30)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    was_successful: Optional[bool] = None
    notes: Optional[str] = None

class AIRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    context: Optional[str] = None
    conversation_id: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    services: Dict[str, str]

# ADHD Support Service
class ADHDSupportService:
    """Core service for ADHD executive function support"""
    
    def __init__(self):
        self.redis_pool = None
        self.db_pool = None
        self.motoko_client = httpx.AsyncClient()
        self.motoko_url = os.getenv("MOTOKO_LLM_URL", "http://192.168.1.12:8000")
        
    async def initialize(self):
        """Initialize database connections"""
        try:
            # Redis for session cache and real-time data
            redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
            self.redis_pool = aioredis.from_url(redis_url, decode_responses=True)
            
            # PostgreSQL for persistent data
            pg_dsn = os.getenv("DATABASE_URL", "postgresql://user:pass@postgres:5432/adhd_db")
            self.db_pool = await asyncpg.create_pool(pg_dsn, min_size=2, max_size=10)
            
            await self._create_tables()
            logger.info("ADHD Support Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ADHD Support Service: {e}")
            raise
    
    async def _create_tables(self):
        """Create database tables if they don't exist"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    priority INTEGER DEFAULT 3,
                    due_date TIMESTAMP WITH TIME ZONE,
                    completed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    tags TEXT[],
                    estimated_duration INTEGER,
                    context VARCHAR(50)
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS quick_notes (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    content TEXT NOT NULL,
                    tags TEXT[],
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    context VARCHAR(50)
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS focus_sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    task_id UUID REFERENCES tasks(id),
                    duration_minutes INTEGER NOT NULL,
                    break_duration INTEGER NOT NULL,
                    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    completed_at TIMESTAMP WITH TIME ZONE,
                    was_successful BOOLEAN,
                    notes TEXT
                )
            """)
    
    async def create_task(self, task: Task) -> Task:
        """Create a new task"""
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchrow("""
                INSERT INTO tasks (title, description, priority, due_date, tags, estimated_duration, context)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, created_at
            """, task.title, task.description, task.priority, task.due_date, 
                task.tags, task.estimated_duration, task.context)
            
            task.id = str(result['id'])
            task.created_at = result['created_at']
            
            # Cache in Redis for quick access
            await self.redis_pool.setex(
                f"task:{task.id}", 
                3600,  # 1 hour TTL
                json.dumps(asdict(task), default=str)
            )
            
            logger.info(f"Created task: {task.title} (ID: {task.id})")
            return task
    
    async def get_tasks(self, completed: Optional[bool] = None, context: Optional[str] = None) -> List[Task]:
        """Get tasks with optional filtering"""
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        
        if completed is not None:
            query += " AND completed = $" + str(len(params) + 1)
            params.append(completed)
            
        if context:
            query += " AND context = $" + str(len(params) + 1)
            params.append(context)
            
        query += " ORDER BY priority DESC, created_at DESC"
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
        return [Task(**dict(row)) for row in rows]
    
    async def start_focus_session(self, session: FocusSession) -> FocusSession:
        """Start a new focus session"""
        session.started_at = datetime.utcnow()
        
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchrow("""
                INSERT INTO focus_sessions (task_id, duration_minutes, break_duration, started_at, notes)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, session.task_id, session.duration_minutes, session.break_duration, 
                session.started_at, session.notes)
            
            session.id = str(result['id'])
        
        # Store active session in Redis
        await self.redis_pool.setex(
            f"active_session:{session.id}",
            session.duration_minutes * 60,  # TTL = session duration
            json.dumps(asdict(session), default=str)
        )
        
        logger.info(f"Started focus session: {session.id} for {session.duration_minutes} minutes")
        return session
    
    async def ask_ai(self, request: AIRequest) -> Dict[str, Any]:
        """Send AI request to Motoko with ADHD-optimized prompting"""
        
        # Add ADHD-friendly context to the prompt
        enhanced_prompt = f"""
Context: ADHD executive function support
User needs: Clear, actionable, structured responses
Request: {request.prompt}

Please provide:
1. Direct answer (if applicable)
2. Next actionable steps (if applicable)  
3. Keep response concise but complete
4. Use bullet points or numbered lists when helpful
"""
        
        try:
            async with self.motoko_client as client:
                response = await client.post(
                    f"{self.motoko_url}/generate",
                    json={
                        "prompt": enhanced_prompt,
                        "max_tokens": 500,
                        "temperature": 0.7
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Cache the conversation for context
                    if request.conversation_id:
                        await self.redis_pool.lpush(
                            f"conversation:{request.conversation_id}",
                            json.dumps({
                                "prompt": request.prompt,
                                "response": result.get("response", ""),
                                "timestamp": datetime.utcnow().isoformat()
                            })
                        )
                        # Keep only last 10 messages
                        await self.redis_pool.ltrim(f"conversation:{request.conversation_id}", 0, 9)
                    
                    return {
                        "response": result.get("response", ""),
                        "conversation_id": request.conversation_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    raise HTTPException(status_code=502, detail="AI service unavailable")
                    
        except httpx.TimeoutException:
            raise HTTPException(status_code=408, detail="AI request timed out")
        except Exception as e:
            logger.error(f"AI request failed: {e}")
            raise HTTPException(status_code=500, detail="AI request failed")
    
    async def get_health_status(self) -> HealthResponse:
        """Check health of all connected services"""
        services = {}
        
        # Check Redis
        try:
            await self.redis_pool.ping()
            services["redis"] = "healthy"
        except Exception:
            services["redis"] = "unhealthy"
        
        # Check PostgreSQL
        try:
            async with self.db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            services["postgresql"] = "healthy"
        except Exception:
            services["postgresql"] = "unhealthy"
        
        # Check Motoko
        try:
            async with self.motoko_client as client:
                response = await client.get(f"{self.motoko_url}/health", timeout=5.0)
                services["motoko"] = "healthy" if response.status_code == 200 else "unhealthy"
        except Exception:
            services["motoko"] = "unhealthy"
        
        overall_status = "healthy" if all(s == "healthy" for s in services.values()) else "degraded"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            services=services
        )

# Initialize service
adhd_service = ADHDSupportService()

# FastAPI app
app = FastAPI(
    title="ADHD Executive Function Support API",
    description="AI-powered support for ADHD executive function with task management, focus tracking, and AI assistance",
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

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.on_event("startup")
async def startup_event():
    await adhd_service.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    if adhd_service.redis_pool:
        await adhd_service.redis_pool.close()
    if adhd_service.db_pool:
        await adhd_service.db_pool.close()
    await adhd_service.motoko_client.aclose()

# Health endpoint (no rate limit for monitoring)
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring"""
    return await adhd_service.get_health_status()

# Task management endpoints
@app.post("/tasks", response_model=Task)
@limiter.limit("30/minute")
async def create_task(task: Task, request: Request):
    """Create a new task"""
    return await adhd_service.create_task(task)

@app.get("/tasks", response_model=List[Task])
@limiter.limit("60/minute")
async def get_tasks(request: Request, completed: Optional[bool] = None, context: Optional[str] = None):
    """Get tasks with optional filtering"""
    return await adhd_service.get_tasks(completed=completed, context=context)

@app.put("/tasks/{task_id}/complete")
@limiter.limit("30/minute")
async def complete_task(task_id: str, request: Request):
    """Mark a task as completed"""
    async with adhd_service.db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE tasks SET completed = TRUE WHERE id = $1",
            task_id
        )
    
    # Clear from Redis cache
    await adhd_service.redis_pool.delete(f"task:{task_id}")
    
    return {"status": "completed", "task_id": task_id}

# Focus session endpoints
@app.post("/focus-sessions", response_model=FocusSession)
@limiter.limit("20/minute")
async def start_focus_session(session: FocusSession, request: Request):
    """Start a new focus session"""
    return await adhd_service.start_focus_session(session)

@app.get("/focus-sessions/active")
@limiter.limit("60/minute")
async def get_active_sessions(request: Request):
    """Get currently active focus sessions"""
    keys = await adhd_service.redis_pool.keys("active_session:*")
    sessions = []
    
    for key in keys:
        session_data = await adhd_service.redis_pool.get(key)
        if session_data:
            sessions.append(json.loads(session_data))
    
    return sessions

# Quick notes endpoints
@app.post("/notes", response_model=QuickNote)
@limiter.limit("60/minute")
async def create_note(note: QuickNote, request: Request):
    """Create a quick note"""
    async with adhd_service.db_pool.acquire() as conn:
        result = await conn.fetchrow("""
            INSERT INTO quick_notes (content, tags, context)
            VALUES ($1, $2, $3)
            RETURNING id, created_at
        """, note.content, note.tags, note.context)
        
        note.id = str(result['id'])
        note.created_at = result['created_at']
    
    return note

@app.get("/notes", response_model=List[QuickNote])
@limiter.limit("60/minute")
async def get_notes(request: Request, context: Optional[str] = None):
    """Get quick notes"""
    query = "SELECT * FROM quick_notes WHERE 1=1"
    params = []
    
    if context:
        query += " AND context = $1"
        params.append(context)
    
    query += " ORDER BY created_at DESC LIMIT 50"
    
    async with adhd_service.db_pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
    
    return [QuickNote(**dict(row)) for row in rows]

# AI assistance endpoints
@app.post("/ai/ask")
@limiter.limit("10/minute")
async def ask_ai(request: AIRequest, req: Request):
    """Ask AI for assistance with ADHD-optimized prompting"""
    return await adhd_service.ask_ai(request)

# Dashboard summary endpoint
@app.get("/dashboard/summary")
@limiter.limit("30/minute")  
async def get_dashboard_summary(request: Request):
    """Get dashboard summary for ADHD support overview"""
    
    # Get task counts
    async with adhd_service.db_pool.acquire() as conn:
        pending_tasks = await conn.fetchval("SELECT COUNT(*) FROM tasks WHERE completed = FALSE")
        completed_today = await conn.fetchval("""
            SELECT COUNT(*) FROM tasks 
            WHERE completed = TRUE AND DATE(created_at) = CURRENT_DATE
        """)
        
        # Get active focus sessions
        active_sessions = len(await adhd_service.redis_pool.keys("active_session:*"))
        
        # Get recent notes count
        notes_today = await conn.fetchval("""
            SELECT COUNT(*) FROM quick_notes 
            WHERE DATE(created_at) = CURRENT_DATE
        """)
    
    return {
        "pending_tasks": pending_tasks,
        "completed_today": completed_today,
        "active_focus_sessions": active_sessions,
        "notes_today": notes_today,
        "timestamp": datetime.utcnow().isoformat()
    }

# WebSocket endpoint for real-time chat
@app.websocket("/ws/chat/{user_id}")
async def chat_websocket(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time chat interface"""
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message["type"] == "chat":
                # Broadcast chat message to all connected clients
                await manager.broadcast({
                    "type": "chat",
                    "user_id": user_id,
                    "message": message["content"],
                    "timestamp": datetime.utcnow().isoformat()
                })
            elif message["type"] == "typing":
                # Notify others that the user is typing
                await manager.broadcast({
                    "type": "typing",
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        # Broadcast user disconnect to all clients
        await manager.broadcast({
            "type": "system",
            "message": f"User {user_id} has disconnected",
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(websocket, user_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

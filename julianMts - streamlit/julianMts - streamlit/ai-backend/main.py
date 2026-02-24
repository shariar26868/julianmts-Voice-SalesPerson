
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.database import mongodb
from app.routes import salesperson, company, meeting, conversation

# Create FastAPI app
app = FastAPI(
    title="AI Sales Training Platform",
    description="Multi-agent AI conversation platform for sales training",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Startup & Shutdown events
# -------------------------

@app.on_event("startup")
async def startup_db():
    await mongodb.connect_db()
    print("🚀 AI Sales Training Platform started")

@app.on_event("shutdown")
async def shutdown_db():
    await mongodb.close_db()
    print("🛑 AI Sales Training Platform stopped")

# -------------------------
# Health checks
# -------------------------

@app.get("/")
async def root():
    return {
        "message": "AI Sales Training Platform API",
        "status": "running",
        "version": "1.0.0",
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
    }

# -------------------------
# API Routes
# -------------------------

app.include_router(salesperson.router, prefix="/salespersons", tags=["Salesperson"])
app.include_router(company.router, prefix="/companies", tags=["Company"])
app.include_router(meeting.router, prefix="/meetings", tags=["Meeting"])
app.include_router(conversation.router, prefix="/conversations", tags=["Conversation"])

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from app.config.database import mongodb
# from app.routes import salesperson, company, meeting, conversation
# import uvicorn

# # Create FastAPI app
# app = FastAPI(
#     title="AI Sales Training Platform",
#     description="Multi-agent AI conversation platform for sales training",
#     version="1.0.0"
# )

# # CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # In production, specify exact origins
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# # Startup event
# @app.on_event("startup")
# async def startup_db():
#     """Connect to MongoDB on startup"""
#     await mongodb.connect_db()
#     print("🚀 AI Sales Training Platform is running!")


# # Shutdown event
# @app.on_event("shutdown")
# async def shutdown_db():
#     """Close MongoDB connection on shutdown"""
#     await mongodb.close_db()


# # Health check endpoint
# @app.get("/")
# async def root():
#     return {
#         "message": "AI Sales Training Platform API",
#         "status": "running",
#         "version": "1.0.0"
#     }


# @app.get("/health")
# async def health_check():
#     return {
#         "status": "healthy",
#         "database": "connected"
#     }


# # Include routers
# app.include_router(salesperson.router)
# app.include_router(company.router)
# app.include_router(meeting.router)
# app.include_router(conversation.router)


# # Run the application
# if __name__ == "__main__":
#     uvicorn.run(
#         "app.main:app",
#         host="0.0.0.0",
#         port=8000,
#         reload=True
#     )




from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.database import mongodb
from app.routes import salesperson, company, meeting, conversation
from app.routes import admin
from app.routes import methodology
from app.routes import opportunities
app = FastAPI(
    title="AI Sales Training Platform",
    description="Multi-agent AI conversation platform for sales training",
    version="1.0.0",
)

# CORS middleware
# NOTE: allow_credentials=True is INCOMPATIBLE with allow_origins=["*"].
# Using wildcard origin requires allow_credentials=False.
# If cookies/auth headers are needed, replace ["*"] with explicit origin list.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Startup & Shutdown events
# -------------------------

@app.on_event("startup")
async def startup_db():
    await mongodb.connect_db()
    from app.config.settings import settings
    print(f"🚀 AI Sales Training Platform started | DB: {settings.MONGODB_DB_NAME}")

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

app.include_router(salesperson.router, tags=["Salesperson"])
app.include_router(company.router, tags=["Company"])
app.include_router(meeting.router, tags=["Meeting"])
app.include_router(conversation.router, tags=["Conversation"])
app.include_router(admin.router)
app.include_router(methodology.router, prefix="/api/methodology", tags=["Methodology"])
app.include_router(opportunities.router, prefix="/api/opportunities", tags=["Opportunities"])


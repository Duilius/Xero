from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import Settings
from app.api import auth, users, orgs, xero
from app.core.middlewares import AuthMiddleware
from app.core.template_filters import format_number

app = FastAPI(
    title="Xero Data Extractor",
    description="Cloud service for Xero data extraction and analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://xero.dataextractor.cloud"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication Middleware
app.middleware("http")(AuthMiddleware())

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Add custom filters
templates.env.filters["format_number"] = format_number

# Root path
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "current_year": datetime.now().year
        }
    )

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(orgs.router, prefix="/organizations", tags=["Organizations"])
app.include_router(xero.router, prefix="/api", tags=["Xero Integration"])

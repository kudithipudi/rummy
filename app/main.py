from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from .api import auth, game
from .config import settings

app = FastAPI(title="Rummy Score Tracker")

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(game.router, prefix="/game", tags=["game"])

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")


# Add base_path to all template contexts
def get_template_context(request: Request, **kwargs):
    """Create template context with base_path included"""
    return {
        "request": request,
        "base_path": settings.base_path,
        **kwargs
    }


@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """Homepage with rummy instructions and track scores button"""
    return templates.TemplateResponse("public/index.html", get_template_context(request))
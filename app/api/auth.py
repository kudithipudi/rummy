from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import timedelta
from ..services.auth import auth_service
from ..services.email import email_service
from ..models.schemas import UserBase
from ..config import settings

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_template_context(request: Request, **kwargs):
    """Create template context with base_path included"""
    return {
        "request": request,
        "base_path": settings.base_path,
        **kwargs
    }


@router.get("/login")
async def login_page(request: Request):
    """Display login page"""
    return templates.TemplateResponse("auth/login.html", get_template_context(request))


@router.post("/magic-link")
async def send_magic_link(user_data: UserBase):
    """Send magic link for authentication"""

    # Validate email
    is_valid, error_msg = email_service.validate_email(user_data.email)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Create access token
    token = auth_service.create_access_token(
        user_data.email,
        expires_delta=timedelta(days=7)
    )

    # Create magic link (full URL for email)
    magic_link = f"{settings.app_url}{settings.base_path}/auth/callback?token={token}"

    # Build redirect URL (relative path for immediate login)
    redirect_url = f"{settings.base_path}/auth/callback?token={token}"

    # Send email (non-blocking - user can access via redirect even if email fails)
    email_service.send_magic_link(user_data.email, magic_link)

    return {"message": "Magic link sent to your email", "redirect_url": redirect_url}


@router.get("/callback")
async def auth_callback(request: Request, token: str):
    """Handle magic link callback"""

    try:
        # Verify token and get user
        email = auth_service.verify_token(token)
        user = await auth_service.get_or_create_user(email)

        # Create new authenticated token
        auth_token = auth_service.create_access_token(email)

        # Redirect to dashboard with token in cookie
        response = RedirectResponse(url=f"{settings.base_path}/game/dashboard", status_code=302)
        response.set_cookie(
            key="auth_token",
            value=auth_token,
            max_age=7*24*3600,  # 7 days
            httponly=True,
            samesite="lax"
        )
        return response

    except Exception as e:
        return templates.TemplateResponse("auth/error.html", get_template_context(
            request,
            error=str(e)
        ))


@router.get("/logout")
async def logout():
    """Logout user"""
    response = RedirectResponse(url=f"{settings.base_path}/", status_code=302)
    response.delete_cookie(key="auth_token")
    return response
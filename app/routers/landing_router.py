from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.security import decode_access_token

router = APIRouter(tags=["pages"])

templates = Jinja2Templates(directory="app/templates")

def get_optional_user(request: Request):
    token = request.cookies.get("access_token")
    if token:
        payload = decode_access_token(token)
        if payload and payload.get("sub"):
            return payload.get("sub")
    return None

@router.get("/", response_class=HTMLResponse)
async def read_landing(request: Request):
    user_id = get_optional_user(request)
    if user_id:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="index.html")

@router.get("/login", response_class=HTMLResponse)
async def read_login(request: Request):
    user_id = get_optional_user(request)
    if user_id:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="login.html")

@router.get("/register", response_class=HTMLResponse)
async def read_register(request: Request):
    user_id = get_optional_user(request)
    if user_id:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="register.html")

@router.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    user_id = get_optional_user(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="dashboard.html")

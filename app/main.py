from fastapi import FastAPI, UploadFile, HTTPException, Request, Form, Depends
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
import os
import asyncio
import logging
from pathlib import Path
from .shazam import recognize_song
from .duckduckgo import search_track
from typing import List, Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from .database import get_db_connection, create_user_simple, check_user_simple, get_user_by_login, save_track, get_user_tracks, get_all_discussions, get_discussion_stats, get_discussion, get_comments, add_comment, create_discussion, get_all_comments, delete_comment
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
import logging

from .database import (
    get_db_connection,
    create_user_simple,  
    check_user_simple,    
    get_user_by_login,
    save_track,
    get_user_tracks,
    get_discussion_stats,
    get_all_discussions,
    get_comments,
    get_discussion,
    add_comment,
    create_discussion,
    get_all_comments,
    delete_comment
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


Path("static").mkdir(exist_ok=True)
Path("templates").mkdir(exist_ok=True)

def is_admin(user: dict) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return user.get("is_admin", False)

class SearchRequest(BaseModel):
    query: str
    genres: Optional[List[str]] = None
    limit: int = 5


class TrackCreateRequest(BaseModel):
    title: str
    artist: str
    is_original: bool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Music Analyzer")

templates = Jinja2Templates(directory="templates")

current_user = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key="electrobreaker",  
    session_cookie="soundhome_session"
)
class LoginRequest(BaseModel):
    login: str
    password: str


def check_user(login: str, password: str) -> bool:

    logger.info(f"Попытка входа пользователя: {login}")
    return True  

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    current_user = request.session.get("username")
    logger.info(f"Текущий пользователь: {current_user or 'не авторизован'}")
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "current_user": current_user
    })


@app.post("/api/recognize")
async def analyze_music(file: UploadFile, request: Request):
    logger.info("File received: %s", file.filename)
    
    temp_file = f"temp_{file.filename}"
    try:
        with open(temp_file, "wb") as buffer:
            buffer.write(await file.read())
        
        shazam_data = await recognize_song(temp_file)
        if not shazam_data:
            return JSONResponse({
                "status": "original",
                "message": "Трек оригинален",
                "originality_score": 100
            })

     
        try:
            search_results = search_track(title=shazam_data["title"], artist=shazam_data["artist"])
            
            if search_results is None:  
                originality = "unknown"
                message = "Не удалось проверить на платформах"
                originality_score = 50
            else:
                originality = "common" if len(search_results) >= 2 else "original"
                message = ("Трек найден на популярных платформах" if originality == "common" 
                          else "Трек оригинален (не найден на музыкальных платформах)")
                originality_score = 0 if originality == "common" else 80
            
          
            username = request.session.get("username")
            if username and originality == "common":
                user = get_user_by_login(username)
                if user:
                    save_track(
                        user_id=user["id"],
                        title=shazam_data["title"],
                        artist=shazam_data["artist"],
                        is_original=False
                    )
            
            return JSONResponse({
                "status": "success",
                "originality": originality,
                "message": message,
                "metadata": shazam_data,
                "search_results": search_results if search_results else [],
                "originality_score": originality_score
            })
        except Exception as search_error:
            logger.error(f"Search error: {search_error}")
            return JSONResponse({
                "status": "search_failed",
                "message": "Ошибка при проверке на платформах",
                "metadata": shazam_data,
                "originality_score": 50
            })


    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обработки файла")
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
@app.post("/register")
async def register(
    request: Request,
    login: str = Form(...),
    password: str = Form(...)
):
    if len(login) < 8:
        return templates.TemplateResponse("registration.html", {
            "request": request,
            "error": "Логин должен быть не менее 8 символов"
        })
    
    if create_user_simple(login, password):
        global current_user
        current_user = login
        return RedirectResponse("/", status_code=303)
    else:
        return templates.TemplateResponse("registration.html", {
            "request": request,
            "error": "Логин уже занят"
        })
@app.get("/users")
async def get_users():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return {"users": users}

@app.post("/login")
async def login(
    request: Request,
    login: str = Form(...),
    password: str = Form(...)
):
    if check_user(login, password):
        request.session["username"] = login
        logger.info(f"Успешная авторизация: {login}")
        return RedirectResponse(url="/", status_code=303)  
    else:
        logger.warning(f"Ошибка авторизации для: {login}")
        return JSONResponse(
            {"detail": "Неверный логин или пароль"}, 
            status_code=400
        )


@app.get("/logout")
async def logout(request: Request):
    username = request.session.get("username")
    if username:
        logger.info(f"Пользователь {username} вышел из системы")
        request.session.clear()
    return RedirectResponse("/")

@app.get("/auth", response_class=HTMLResponse)
async def auth_page(request: Request):
    return templates.TemplateResponse("registration.html", {"request": request})


@app.get("/profile", response_class=HTMLResponse)
async def user_profile(request: Request):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/auth")
    
    user = get_user_by_login(username)
    if not user:
        return RedirectResponse(url="/auth")
    
    tracks = get_user_tracks(user["id"])
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "current_user": username,
        "tracks": tracks,
        "user_info": user
    })
@app.get("/forum", response_class=HTMLResponse)
async def forum_page(request: Request):
    discussions = get_all_discussions()
    return templates.TemplateResponse("forum.html", {
        "request": request,
        "current_user": request.session.get("username"),
        "discussions": discussions
    })

@app.get("/forum/new", response_class=HTMLResponse)
async def new_discussion_page(request: Request):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/auth")
    
    user = get_user_by_login(username)
    if not user:
        return RedirectResponse(url="/auth")
    
    tracks = get_user_tracks(user["id"])
    
    return templates.TemplateResponse("new_discussion.html", {
        "request": request,
        "current_user": username,
        "tracks": [t for t in tracks if not t["is_original"]]
    })

@app.post("/forum/create")
async def create_discussion_endpoint(
    request: Request,
    track_id: int = Form(...),
    title: str = Form(...)
):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = get_user_by_login(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
 
    discussion_id = create_discussion(track_id, user["id"], title)
    
    if discussion_id:
        return RedirectResponse(url=f"/forum/{discussion_id}", status_code=303)
    else:
        raise HTTPException(status_code=500, detail="Failed to create discussion")
    
@app.get("/forum/{discussion_id}", response_class=HTMLResponse)
async def view_discussion(request: Request, discussion_id: int):
    discussion = get_discussion(discussion_id)
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")
    
    comments = get_comments(discussion_id)
    
    return templates.TemplateResponse("discussion.html", {
        "request": request,
        "current_user": request.session.get("username"),
        "discussion": discussion,
        "comments": comments
    })

@app.post("/forum/{discussion_id}/comment")
async def add_comment_to_discussion(
    request: Request,
    discussion_id: int,
    content: str = Form(...)
):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = get_user_by_login(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    success = add_comment(
        discussion_id=discussion_id,
        user_id=user["id"],
        content=content
    )
    
    if success:
        return RedirectResponse(url=f"/forum/{discussion_id}", status_code=303)
    else:
        raise HTTPException(status_code=500, detail="Failed to add comment")
    
@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/auth")
    
    user = get_user_by_login(username)
    if not user or not is_admin(user):
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    
    comments = get_all_comments()
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "comments": comments
    })

@app.delete("/admin/comments/{comment_id}")
async def delete_comment_endpoint(comment_id: int, request: Request):
   
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401)
    
    user = get_user_by_login(username)
    if not user or not is_admin(user):
        raise HTTPException(status_code=403)
    
   
    if delete_comment(comment_id):
        return {"status": "success"}
    else:
        raise HTTPException(status_code=500, detail="Ошибка при удалении")
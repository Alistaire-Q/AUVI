import os
import httpx
from datetime import datetime
from typing import Dict, Any

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
# In production, this should be the frontend URL or the backend callback URL.
# Since it's an API, the backend handles the callback and then redirects to the frontend.
REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/youtube/callback")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/userinfo.email"
]

def get_auth_url() -> str:
    scope_str = "%20".join(SCOPES)
    url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"response_type=code&"
        f"scope={scope_str}&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    return url


async def exchange_code(code: str) -> Dict[str, Any]:
    url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)
        response.raise_for_status()
        return response.json()


async def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
    url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)
        response.raise_for_status()
        return response.json()


async def get_user_info(access_token: str) -> Dict[str, Any]:
    url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()


async def get_channel_info(access_token: str) -> Dict[str, Any]:
    url = "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data.get("items"):
            return {
                "id": data["items"][0]["id"],
                "title": data["items"][0]["snippet"]["title"]
            }
        return {"id": None, "title": "Unknown Channel"}


async def upload_video_to_shorts(access_token: str, file_path: str, title: str, description: str, tags: list = None) -> str:
    """
    Uploads a video to YouTube using the v3 API and returns the video ID.
    """
    if tags is None:
        tags = ["Shorts", "AUVI"]
    else:
        if "Shorts" not in tags:
            tags.append("Shorts")
    
    url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
    
    metadata = {
        "snippet": {
            "title": title,
            "description": f"{description}\n\n#Shorts",
            "tags": tags,
            "categoryId": "24"  # Entertainment
        },
        "status": {
            "privacyStatus": "private",  # Upload as private first for safety, or 'public'
            "selfDeclaredMadeForKids": False
        }
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Upload-Content-Length": str(os.path.getsize(file_path)),
    }
    
    async with httpx.AsyncClient() as client:
        # Step 1: Initialize resumable upload
        init_res = await client.post(url, headers=headers, json=metadata)
        init_res.raise_for_status()
        upload_url = init_res.headers.get("Location")
        
        if not upload_url:
            raise Exception("Failed to get upload URL from YouTube API")
            
        # Step 2: Upload the actual video file
        with open(file_path, "rb") as f:
            file_data = f.read()
            
        upload_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/octet-stream"
        }
        
        upload_res = await client.put(upload_url, headers=upload_headers, content=file_data, timeout=300.0)
        upload_res.raise_for_status()
        
        result_data = upload_res.json()
        return result_data.get("id")

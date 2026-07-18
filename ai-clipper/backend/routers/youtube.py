from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import get_db
from models.schemas import LinkedAccount, Job, PreferencesSchema
from services import youtube_api

router = APIRouter(prefix="/api/youtube", tags=["youtube"])

@router.get("/login")
async def login_youtube():
    """Redirects the user to Google OAuth consent screen."""
    url = youtube_api.get_auth_url()
    return RedirectResponse(url)

@router.get("/callback")
async def youtube_callback(code: str, db: Session = Depends(get_db)):
    """Handles the OAuth callback, exchanges code for tokens, and saves to DB."""
    try:
        token_data = await youtube_api.exchange_code(code)
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to retrieve access token")
            
        # Get channel info to store
        channel_info = await youtube_api.get_channel_info(access_token)
        channel_id = channel_info.get("id")
        channel_name = channel_info.get("title")
        
        # Upsert LinkedAccount
        account = db.query(LinkedAccount).filter(LinkedAccount.channel_id == channel_id).first()
        if not account:
            account = LinkedAccount(
                channel_id=channel_id,
                channel_name=channel_name,
                access_token=access_token,
                refresh_token=refresh_token
            )
            db.add(account)
        else:
            account.access_token = access_token
            if refresh_token:
                account.refresh_token = refresh_token
                
        db.commit()
        
        # Redirect back to frontend settings/integration page
        return RedirectResponse(f"{youtube_api.FRONTEND_URL}/integrations?success=true")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth failed: {str(e)}")

@router.get("/status")
async def get_connection_status(db: Session = Depends(get_db)):
    """Check if there is a linked YouTube account."""
    account = db.query(LinkedAccount).first()
    if account:
        return {"linked": True, "channel_name": account.channel_name}
    return {"linked": False}

@router.post("/disconnect")
async def disconnect_youtube(db: Session = Depends(get_db)):
    """Remove linked accounts."""
    db.query(LinkedAccount).delete()
    db.commit()
    return {"status": "success", "message": "Account disconnected"}

@router.get("/preferences")
async def get_preferences(db: Session = Depends(get_db)):
    """Get creator preferences."""
    account = db.query(LinkedAccount).first()
    if not account:
        raise HTTPException(status_code=404, detail="No linked account")
    return account.preferences or {}

@router.put("/preferences")
async def update_preferences(prefs: PreferencesSchema, db: Session = Depends(get_db)):
    """Update creator preferences."""
    account = db.query(LinkedAccount).first()
    if not account:
        raise HTTPException(status_code=404, detail="No linked account")
    
    account.preferences = prefs.model_dump()
    db.commit()
    return {"status": "success", "preferences": account.preferences}

# --- WEBHOOK ENDPOINTS ---
@router.get("/webhook")
async def verify_webhook(request: Request):
    """
    PubSubHubbub verification endpoint.
    YouTube will send a GET request with hub.challenge to verify the webhook.
    """
    mode = request.query_params.get("hub.mode")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and challenge:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=400, detail="Invalid request")

@router.post("/webhook")
async def receive_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Receive video push notification from YouTube PubSubHubbub.
    """
    body = await request.body()
    # In a real app, you would parse the ATOM XML feed here.
    # For now, let's assume we can parse it and get the video URL.
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(body)
        
        # Find the video ID (Atom namespace usually)
        namespace = {'yt': 'http://www.youtube.com/xml/schemas/2015', 'atom': 'http://www.w3.org/2005/Atom'}
        video_id_el = root.find('.//yt:videoId', namespace)
        
        if video_id_el is not None and video_id_el.text:
            video_id = video_id_el.text
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Check if this job already exists
            existing_job = db.query(Job).filter(Job.url == video_url).first()
            if not existing_job:
                # Find channel ID to get preferences
                channel_id_el = root.find('.//yt:channelId', namespace)
                channel_id = channel_id_el.text if channel_id_el is not None else None
                
                settings = {}
                if channel_id:
                    account = db.query(LinkedAccount).filter(LinkedAccount.channel_id == channel_id).first()
                    if account and account.preferences:
                        settings = account.preferences
                else:
                    account = db.query(LinkedAccount).first()
                    if account and account.preferences:
                        settings = account.preferences

                from models.schemas import Job
                
                # Create a Job record
                new_job = Job(
                    source_type="webhook",
                    url=video_url,
                    settings=settings
                )
                db.add(new_job)
                db.commit()
                db.refresh(new_job)

                from arq.connections import create_pool
                from redis_client import get_redis_settings
                redis = await create_pool(get_redis_settings())
                await redis.enqueue_job("process_video_pipeline", new_job.id)
                print(f"Enqueued new video from webhook: {video_url} with job ID: {new_job.id}")
                    
        return Response(status_code=200)
    except Exception as e:
        print(f"Error parsing webhook: {e}")
        return Response(status_code=200) # Always return 200 to acknowledge receipt

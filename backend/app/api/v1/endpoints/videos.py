"""
SafeVision AI - Video Upload, Processing, and Evidence Endpoints
"""

import os
import uuid
import aiofiles
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, status, BackgroundTasks, Depends
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.database.session import get_db
from backend.app.models.incident import Incident
from backend.app.schemas.video import (
    VideoUploadResponse,
    VideoProcessingStatusResponse,
    VideoAnalysisResultResponse,
    IncidentDetectionResponse,
    EvidenceItemResponse,
)
from backend.app.services.video_processing import video_service

router = APIRouter()

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB


@router.post(
    "/videos/upload",
    response_model=VideoUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload surveillance video file"
)
async def upload_video(file: UploadFile = File(...)):
    """
    Uploads an actual surveillance video file for real AI safety analysis.
    Validates extension and file size, saves to storage/videos/.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video format '{ext}'. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    video_id = str(uuid.uuid4())[:12]
    clean_filename = f"{video_id}_{os.path.basename(file.filename)}"
    storage_dir = settings.VIDEO_STORAGE_PATH
    os.makedirs(storage_dir, exist_ok=True)
    target_path = os.path.join(storage_dir, clean_filename)

    file_size = 0
    try:
        async with aiofiles.open(target_path, "wb") as out_file:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="Video file exceeds maximum allowed size (500MB)."
                    )
                await out_file.write(chunk)
    except HTTPException:
        if os.path.exists(target_path):
            os.remove(target_path)
        raise
    except Exception as e:
        logger.exception(f"Error saving uploaded file: {e}")
        if os.path.exists(target_path):
            os.remove(target_path)
        raise HTTPException(status_code=500, detail="Failed to save video file to storage.")

    # Register in processing manager
    video_service.register_video(video_id, target_path, file.filename)

    return VideoUploadResponse(
        video_id=video_id,
        filename=file.filename,
        file_size_bytes=file_size,
        video_url=f"/api/v1/videos/{video_id}/stream",
        uploaded_at=datetime.now(timezone.utc)
    )


@router.post(
    "/videos/{video_id}/process",
    response_model=VideoAnalysisResultResponse,
    summary="Process video for fall detection"
)
async def process_video_endpoint(video_id: str):
    """
    Executes real YOLO Pose inference and 3-State Evidence Reasoning on the video.
    """
    status_info = video_service.get_status(video_id)
    if not status_info:
        raise HTTPException(status_code=404, detail=f"Video job '{video_id}' not found.")

    try:
        result = video_service.process_video(video_id)
        return result
    except Exception as e:
        logger.exception(f"Video processing failed for {video_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Video processing failed: {str(e)}")


@router.get(
    "/videos/{video_id}/status",
    response_model=VideoProcessingStatusResponse,
    summary="Get video processing progress"
)
async def get_video_status(video_id: str):
    """
    Polls real-time progress of video analysis.
    """
    status_info = video_service.get_status(video_id)
    if not status_info:
        raise HTTPException(status_code=404, detail=f"Video job '{video_id}' not found.")
    return status_info


@router.get(
    "/videos/{video_id}/results",
    response_model=VideoAnalysisResultResponse,
    summary="Get video analysis results"
)
async def get_video_results(video_id: str):
    """
    Retrieves full results of analyzed video.
    """
    result = video_service.get_results(video_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Analysis results for '{video_id}' not found or pending.")
    return result


@router.get(
    "/videos/{video_id}/stream",
    summary="Stream uploaded video"
)
async def stream_video(video_id: str):
    """
    Streams the uploaded video file to the browser HTML5 video player.
    """
    job = video_service._jobs.get(video_id)
    if not job or not os.path.exists(job["filepath"]):
        raise HTTPException(status_code=404, detail="Video file not found.")

    return FileResponse(
        job["filepath"],
        media_type="video/mp4",
        filename=job["filename"]
    )


@router.get(
    "/evidence/{filename}",
    summary="Get evidence snapshot image"
)
async def get_evidence_image(filename: str):
    """
    Serves generated evidence snapshot images with HUD and pose skeleton overlays.
    """
    evidence_path = os.path.join(settings.EVIDENCE_CLIPS_PATH, os.path.basename(filename))
    if not os.path.exists(evidence_path):
        raise HTTPException(status_code=404, detail="Evidence frame not found.")
    return FileResponse(evidence_path, media_type="image/jpeg")


@router.get(
    "/incidents/{incident_id}",
    summary="Get incident details by ID"
)
async def get_incident_by_id(incident_id: int, db: Session = Depends(get_db)):
    """
    Fetches an incident from PostgreSQL along with its evidence records.
    """
    incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident #{incident_id} not found in database.")
    
    return {
        "incident_id": incident.incident_id,
        "event_type": incident.event_type,
        "status": incident.status,
        "confidence": incident.confidence,
        "risk_level": incident.risk_level,
        "start_time": incident.start_time,
        "evidence_items": [
            {
                "evidence_id": e.evidence_id,
                "evidence_type": e.evidence_type,
                "description": e.description,
                "status": e.status,
                "confidence": e.confidence,
                "timestamp": e.timestamp
            }
            for e in incident.evidence_items
        ]
    }

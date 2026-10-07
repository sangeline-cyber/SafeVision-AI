import io
import pytest
from backend.app.schemas.video import VideoUploadResponse


def test_video_upload_invalid_extension(client):
    """
    Tests rejecting unsupported file formats (e.g. .txt, .exe, .pdf).
    """
    file_content = b"Fake text file content"
    response = client.post(
        "/api/v1/videos/upload",
        files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    )
    assert response.status_code == 400
    assert "Unsupported video format" in response.json()["detail"]


def test_video_upload_valid_mp4(client):
    """
    Tests successful upload of a video file with proper metadata response.
    """
    file_content = b"\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2mp41"  # MP4 header bytes
    response = client.post(
        "/api/v1/videos/upload",
        files={"file": ("surveillance_sample.mp4", io.BytesIO(file_content), "video/mp4")}
    )
    assert response.status_code == 201
    data = response.json()
    assert "video_id" in data
    assert data["filename"] == "surveillance_sample.mp4"
    assert "video_url" in data
    assert data["file_size_bytes"] == len(file_content)

    video_id = data["video_id"]

    # Verify status query
    status_res = client.get(f"/api/v1/videos/{video_id}/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["video_id"] == video_id
    assert status_data["status"] in ["pending", "processing", "completed"]


def test_nonexistent_video_endpoints(client):
    """
    Tests 404 behavior for unknown video IDs.
    """
    res1 = client.get("/api/v1/videos/nonexistent_id_123/status")
    assert res1.status_code == 404

    res2 = client.get("/api/v1/videos/nonexistent_id_123/results")
    assert res2.status_code == 404

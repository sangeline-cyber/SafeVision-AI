import axios from 'axios';
import {
  HealthResponse,
  DatabaseHealthResponse,
  VideoUploadResult,
  VideoProcessingStatus,
  VideoAnalysisResult,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes for processing operations
  headers: {
    'Content-Type': 'application/json',
  },
});

export const healthApi = {
  async checkBackendHealth(): Promise<{ data: HealthResponse | null; error: string | null; latencyMs: number }> {
    const start = performance.now();
    try {
      const response = await apiClient.get<HealthResponse>('/api/health');
      const latencyMs = Math.round(performance.now() - start);
      return { data: response.data, error: null, latencyMs };
    } catch (err: any) {
      const latencyMs = Math.round(performance.now() - start);
      const message = err.response?.data?.detail || err.message || 'Failed to connect to backend server';
      return { data: null, error: message, latencyMs };
    }
  },

  async checkDatabaseHealth(): Promise<{ data: DatabaseHealthResponse | null; error: string | null; latencyMs: number }> {
    const start = performance.now();
    try {
      const response = await apiClient.get<DatabaseHealthResponse>('/api/health/database');
      const latencyMs = Math.round(performance.now() - start);
      return { data: response.data, error: null, latencyMs };
    } catch (err: any) {
      const latencyMs = Math.round(performance.now() - start);
      if (err.response?.data) {
        return { data: err.response.data as DatabaseHealthResponse, error: null, latencyMs };
      }
      const message = err.message || 'Failed to query database health endpoint';
      return { data: null, error: message, latencyMs };
    }
  },
};

export const videoApi = {
  /**
   * Uploads real surveillance video file using multipart/form-data.
   */
  async uploadVideo(file: File, onProgress?: (percent: number) => void): Promise<VideoUploadResult> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<VideoUploadResult>('/api/v1/videos/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percent);
        }
      },
    });
    return response.data;
  },

  /**
   * Triggers real YOLO Pose & 3-State Evidence analysis on uploaded video.
   */
  async processVideo(videoId: string): Promise<VideoAnalysisResult> {
    const response = await apiClient.post<VideoAnalysisResult>(`/api/v1/videos/${videoId}/process`);
    return response.data;
  },

  /**
   * Polls live frame-by-frame processing progress.
   */
  async getVideoStatus(videoId: string): Promise<VideoProcessingStatus> {
    const response = await apiClient.get<VideoProcessingStatus>(`/api/v1/videos/${videoId}/status`);
    return response.data;
  },

  /**
   * Retrieves completed video analysis results.
   */
  async getVideoResults(videoId: string): Promise<VideoAnalysisResult> {
    const response = await apiClient.get<VideoAnalysisResult>(`/api/v1/videos/${videoId}/results`);
    return response.data;
  },
};

import axios from 'axios';
import type { Job, JobListResponse, VoiceOption, LanguagesResponse, HealthResponse } from './types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiClient = {
  healthCheck: async (): Promise<HealthResponse> => {
    const response = await api.get<HealthResponse>('/health');
    return response.data;
  },

  uploadVideo: async (
    file: File,
    sourceLanguage: string,
    targetLanguage: string,
    primaryVoice: string,
    secondaryVoice?: string,
    onUploadProgress?: (progress: number) => void
  ): Promise<Job> => {
    const formData = new FormData();
    formData.append('video', file);
    formData.append('source_language', sourceLanguage);
    formData.append('target_language', targetLanguage);
    formData.append('primary_voice', primaryVoice);
    if (secondaryVoice) {
      formData.append('secondary_voice', secondaryVoice);
    }
    formData.append('user_id', 'default_user');

    const response = await api.post<Job>('/jobs/create', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onUploadProgress) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onUploadProgress(percentCompleted);
        }
      },
    });
    return response.data;
  },

  getJob: async (jobId: string): Promise<Job> => {
    const response = await api.get<Job>(`/jobs/${jobId}`);
    return response.data;
  },

  listJobs: async (
    userId: string = 'default_user',
    status?: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<JobListResponse> => {
    const params: Record<string, string | number> = {
      user_id: userId,
      page,
      page_size: pageSize,
    };
    if (status) {
      params.status = status;
    }
    const response = await api.get<JobListResponse>('/jobs', { params });
    return response.data;
  },

  downloadVideo: async (jobId: string): Promise<{ job_id: string; download_url: string; expires_in_hours: number }> => {
    const response = await api.get(`/jobs/${jobId}/download`);
    return response.data;
  },

  cancelJob: async (jobId: string): Promise<{ success: boolean; job_id: string; message: string }> => {
    const response = await api.delete(`/jobs/${jobId}`);
    return response.data;
  },

  retryJob: async (jobId: string): Promise<Job> => {
    const response = await api.post<Job>(`/jobs/${jobId}/retry`);
    return response.data;
  },

  getVoices: async (): Promise<VoiceOption[]> => {
    const response = await api.get<VoiceOption[]>('/voices');
    return response.data;
  },

  getLanguages: async (): Promise<LanguagesResponse> => {
    const response = await api.get<LanguagesResponse>('/languages');
    return response.data;
  },
};

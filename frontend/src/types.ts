export interface Job {
  job_id: string;
  status: JobStatus;
  current_stage: JobStage | null;
  progress_percent: number;
  estimated_time_minutes: number | null;
  download_url: string | null;
  created_at: string;
  updated_at: string;
}

export enum JobStatus {
  QUEUED = 'QUEUED',
  PROCESSING = 'PROCESSING',
  AUDIO_EXTRACTED = 'AUDIO_EXTRACTED',
  TRANSCRIBED = 'TRANSCRIBED',
  TRANSLATED = 'TRANSLATED',
  SYNTHESIZED = 'SYNTHESIZED',
  SYNCHRONIZED = 'SYNCHRONIZED',
  MERGED = 'MERGED',
  VALIDATED = 'VALIDATED',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED',
}

export enum JobStage {
  INTAKE = 'intake',
  AUDIO_EXTRACTION = 'audio_extraction',
  TRANSCRIPTION = 'transcription',
  TRANSLATION = 'translation',
  SPEECH_SYNTHESIS = 'speech_synthesis',
  TIMING_SYNC = 'timing_sync',
  AUDIO_MERGING = 'audio_merging',
  QUALITY_ASSURANCE = 'quality_assurance',
  DELIVERY = 'delivery',
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
  page: number;
  page_size: number;
}

export interface VoiceOption {
  name: string;
  style: string;
  language_support: string[];
  sample_url: string | null;
}

export interface Language {
  code: string;
  name: string;
  tts_support: boolean;
  audio_support: boolean;
}

export interface LanguagesResponse {
  languages: Language[];
}

export interface VoiceConfig {
  primary_voice: string;
  secondary_voice?: string;
  style_preferences?: Record<string, unknown>;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  environment: string;
}

export interface JobProgress {
  job_id: string;
  stage: string;
  progress: number;
  status: 'processing' | 'completed' | 'error';
  message?: string;
}

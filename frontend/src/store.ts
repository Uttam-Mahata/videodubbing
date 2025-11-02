import { create } from 'zustand';
import type { Job, JobStatus } from './types';

interface DubbingState {
  currentJobId: string | null;
  jobStatus: Job | null;
  uploadProgress: number;
  isUploading: boolean;
  sourceLanguage: string;
  targetLanguage: string;
  primaryVoice: string;
  secondaryVoice: string | null;

  setJobId: (jobId: string) => void;
  setJobStatus: (job: Job) => void;
  setUploadProgress: (progress: number) => void;
  setIsUploading: (isUploading: boolean) => void;
  setSourceLanguage: (lang: string) => void;
  setTargetLanguage: (lang: string) => void;
  setPrimaryVoice: (voice: string) => void;
  setSecondaryVoice: (voice: string | null) => void;
  reset: () => void;
}

export const useDubbingStore = create<DubbingState>((set) => ({
  currentJobId: null,
  jobStatus: null,
  uploadProgress: 0,
  isUploading: false,
  sourceLanguage: 'auto',
  targetLanguage: 'es-US',
  primaryVoice: 'Kore',
  secondaryVoice: null,

  setJobId: (jobId) => set({ currentJobId: jobId }),
  setJobStatus: (job) => set({ jobStatus: job }),
  setUploadProgress: (progress) => set({ uploadProgress: progress }),
  setIsUploading: (isUploading) => set({ isUploading }),
  setSourceLanguage: (lang) => set({ sourceLanguage: lang }),
  setTargetLanguage: (lang) => set({ targetLanguage: lang }),
  setPrimaryVoice: (voice) => set({ primaryVoice: voice }),
  setSecondaryVoice: (voice) => set({ secondaryVoice: voice }),
  reset: () =>
    set({
      currentJobId: null,
      jobStatus: null,
      uploadProgress: 0,
      isUploading: false,
    }),
}));

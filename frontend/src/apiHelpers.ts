/**
 * API Helper functions for common patterns
 */

export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
};

export const formatDuration = (seconds: number): string => {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);
  return `${minutes}m ${remainingSeconds}s`;
};

export const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
  
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  
  return date.toLocaleDateString();
};

export const getStatusColor = (status: string): { bg: string; text: string } => {
  const colors: Record<string, { bg: string; text: string }> = {
    COMPLETED: { bg: 'bg-green-100', text: 'text-green-800' },
    FAILED: { bg: 'bg-red-100', text: 'text-red-800' },
    CANCELLED: { bg: 'bg-gray-100', text: 'text-gray-800' },
    QUEUED: { bg: 'bg-yellow-100', text: 'text-yellow-800' },
    PROCESSING: { bg: 'bg-blue-100', text: 'text-blue-800' },
  };
  return colors[status] || { bg: 'bg-gray-100', text: 'text-gray-800' };
};

export const validateVideoFile = (file: File): { valid: boolean; error?: string } => {
  const maxSize = parseInt(import.meta.env.VITE_MAX_FILE_SIZE || '524288000');
  const allowedTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-matroska', 'video/webm'];
  
  if (!allowedTypes.includes(file.type)) {
    return {
      valid: false,
      error: 'Invalid file type. Please upload a video file (MP4, AVI, MOV, MKV, or WebM)',
    };
  }
  
  if (file.size > maxSize) {
    return {
      valid: false,
      error: `File size exceeds ${formatFileSize(maxSize)} limit`,
    };
  }
  
  return { valid: true };
};

export const buildQueryParams = (params: Record<string, string | number | boolean | undefined>): string => {
  const filtered = Object.entries(params).filter(([_, value]) => value !== undefined);
  if (filtered.length === 0) return '';
  
  const queryString = filtered
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
    .join('&');
  
  return `?${queryString}`;
};

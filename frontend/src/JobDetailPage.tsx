import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, RotateCcw, X, AlertCircle } from 'lucide-react';
import { apiClient } from './api';
import { ProgressTracker } from './ProgressTracker';
import { JobStatus } from './types';
import type { Job } from './types';

export function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchJob = async () => {
    if (!jobId) return;
    try {
      const jobData = await apiClient.getJob(jobId);
      setJob(jobData);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch job:', err);
      setError('Failed to load job details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJob();
    const interval = setInterval(fetchJob, 5000);
    return () => clearInterval(interval);
  }, [jobId]);

  const handleDownload = async () => {
    if (!jobId || !job?.download_url) return;
    window.open(job.download_url, '_blank');
  };

  const handleRetry = async () => {
    if (!jobId) return;
    setActionLoading(true);
    try {
      await apiClient.retryJob(jobId);
      await fetchJob();
    } catch (err) {
      console.error('Failed to retry job:', err);
      setError('Failed to retry job');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!jobId) return;
    if (!confirm('Are you sure you want to cancel this job?')) return;

    setActionLoading(true);
    try {
      await apiClient.cancelJob(jobId);
      await fetchJob();
    } catch (err) {
      console.error('Failed to cancel job:', err);
      setError('Failed to cancel job');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading job details...</p>
        </div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error</h2>
          <p className="text-gray-600 mb-4">{error || 'Job not found'}</p>
          <button
            onClick={() => navigate('/jobs')}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Back to Jobs
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-12">
        <button
          onClick={() => navigate('/jobs')}
          className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 mb-6"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>Back to Jobs</span>
        </button>

        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Job {job.job_id.slice(0, 8)}</h1>
              <p className="text-gray-600">
                Created: {new Date(job.created_at).toLocaleString()}
              </p>
            </div>
            <div className="flex space-x-3">
              {job.status === JobStatus.COMPLETED && job.download_url && (
                <button
                  onClick={handleDownload}
                  className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  <Download className="w-5 h-5" />
                  <span>Download</span>
                </button>
              )}
              {job.status === JobStatus.FAILED && (
                <button
                  onClick={handleRetry}
                  disabled={actionLoading}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  <RotateCcw className="w-5 h-5" />
                  <span>Retry</span>
                </button>
              )}
              {(job.status === JobStatus.QUEUED || job.status === JobStatus.PROCESSING) && (
                <button
                  onClick={handleCancel}
                  disabled={actionLoading}
                  className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
                >
                  <X className="w-5 h-5" />
                  <span>Cancel</span>
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <ProgressTracker job={job} />
          </div>

          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Job Details</h3>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-500">Status</p>
                  <p className="font-medium text-gray-900">{job.status}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Progress</p>
                  <p className="font-medium text-gray-900">{job.progress_percent}%</p>
                </div>
                {job.current_stage && (
                  <div>
                    <p className="text-sm text-gray-500">Current Stage</p>
                    <p className="font-medium text-gray-900">{job.current_stage.replace(/_/g, ' ')}</p>
                  </div>
                )}
                {job.estimated_time_minutes && (
                  <div>
                    <p className="text-sm text-gray-500">Estimated Time</p>
                    <p className="font-medium text-gray-900">{job.estimated_time_minutes} minutes</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

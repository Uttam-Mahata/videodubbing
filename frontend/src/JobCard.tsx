import { useNavigate } from 'react-router-dom';
import { Clock, CheckCircle, XCircle, Download, Loader2 } from 'lucide-react';
import { JobStatus } from './types';
import type { Job } from './types';

interface JobCardProps {
  job: Job;
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleString();
};

export function JobCard({ job }: JobCardProps) {
  const navigate = useNavigate();

  const getStatusConfig = (status: JobStatus) => {
    switch (status) {
      case JobStatus.COMPLETED:
        return { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50', label: 'Completed' };
      case JobStatus.FAILED:
        return { icon: XCircle, color: 'text-red-600', bg: 'bg-red-50', label: 'Failed' };
      case JobStatus.CANCELLED:
        return { icon: XCircle, color: 'text-gray-600', bg: 'bg-gray-50', label: 'Cancelled' };
      case JobStatus.QUEUED:
        return { icon: Clock, color: 'text-yellow-600', bg: 'bg-yellow-50', label: 'Queued' };
      default:
        return { icon: Loader2, color: 'text-blue-600', bg: 'bg-blue-50', label: 'Processing' };
    }
  };

  const statusConfig = getStatusConfig(job.status);
  const StatusIcon = statusConfig.icon;

  const handleCardClick = () => {
    navigate(`/jobs/${job.job_id}`);
  };

  const handleDownload = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (job.download_url) {
      window.open(job.download_url, '_blank');
    }
  };

  return (
    <div
      onClick={handleCardClick}
      className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer border border-gray-200"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg ${statusConfig.bg}`}>
            <StatusIcon className={`w-5 h-5 ${statusConfig.color} ${job.status === JobStatus.PROCESSING ? 'animate-spin' : ''}`} />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">Job {job.job_id.slice(0, 8)}</h3>
            <p className="text-sm text-gray-500">{formatDate(job.created_at)}</p>
          </div>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusConfig.bg} ${statusConfig.color}`}>
          {statusConfig.label}
        </span>
      </div>

      {job.current_stage && (
        <div className="mb-4">
          <p className="text-sm text-gray-600 mb-2">Current Stage: {job.current_stage.replace(/_/g, ' ')}</p>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${job.progress_percent}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">{job.progress_percent}% complete</p>
        </div>
      )}

      {job.status === JobStatus.COMPLETED && job.download_url && (
        <button
          onClick={handleDownload}
          className="w-full mt-4 flex items-center justify-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Download className="w-4 h-4" />
          <span>Download</span>
        </button>
      )}

      {job.estimated_time_minutes && job.status === JobStatus.PROCESSING && (
        <p className="text-sm text-gray-600 mt-4">
          Estimated time: {job.estimated_time_minutes} minutes remaining
        </p>
      )}
    </div>
  );
}

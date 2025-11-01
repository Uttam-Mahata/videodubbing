import { CheckCircle2, Circle, Loader2, XCircle } from 'lucide-react';
import { JobStatus, JobStage } from './types';
import type { Job } from './types';

interface ProgressTrackerProps {
  job: Job;
}

const STAGES = [
  { key: 'intake', label: 'Intake' },
  { key: 'audio_extraction', label: 'Audio Extraction' },
  { key: 'transcription', label: 'Transcription' },
  { key: 'translation', label: 'Translation' },
  { key: 'speech_synthesis', label: 'Speech Synthesis' },
  { key: 'timing_sync', label: 'Timing Sync' },
  { key: 'audio_merging', label: 'Audio Merging' },
  { key: 'quality_assurance', label: 'Quality Assurance' },
  { key: 'delivery', label: 'Delivery' },
];

const getStageIndex = (stage: JobStage | null): number => {
  if (!stage) return -1;
  return STAGES.findIndex((s) => s.key === stage);
};

const getStatusIcon = (stageIndex: number, currentStageIndex: number, status: JobStatus) => {
  if (status === JobStatus.FAILED || status === JobStatus.CANCELLED) {
    if (stageIndex <= currentStageIndex) {
      return <XCircle className="w-5 h-5 text-red-500" />;
    }
  }

  if (stageIndex < currentStageIndex) {
    return <CheckCircle2 className="w-5 h-5 text-green-500" />;
  }

  if (stageIndex === currentStageIndex) {
    return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
  }

  return <Circle className="w-5 h-5 text-gray-300" />;
};

export function ProgressTracker({ job }: ProgressTrackerProps) {
  const currentStageIndex = getStageIndex(job.current_stage);

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-900">Processing Progress</h3>
          <span className="text-sm font-medium text-gray-600">{job.progress_percent}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-500 ${
              job.status === JobStatus.FAILED || job.status === JobStatus.CANCELLED
                ? 'bg-red-500'
                : job.status === JobStatus.COMPLETED
                ? 'bg-green-500'
                : 'bg-blue-500'
            }`}
            style={{ width: `${job.progress_percent}%` }}
          />
        </div>
      </div>

      <div className="space-y-4">
        {STAGES.map((stage, index) => {
          const isActive = index === currentStageIndex;
          const isCompleted = index < currentStageIndex;
          const isFailed =
            (job.status === JobStatus.FAILED || job.status === JobStatus.CANCELLED) && index <= currentStageIndex;

          return (
            <div key={stage.key} className="flex items-center space-x-3">
              {getStatusIcon(index, currentStageIndex, job.status)}
              <span
                className={`text-sm ${
                  isActive
                    ? 'font-semibold text-blue-600'
                    : isCompleted
                    ? 'text-green-600'
                    : isFailed
                    ? 'text-red-600'
                    : 'text-gray-400'
                }`}
              >
                {stage.label}
              </span>
            </div>
          );
        })}
      </div>

      {job.estimated_time_minutes && job.status === JobStatus.PROCESSING && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <p className="text-sm text-gray-600">
            Estimated time remaining: <span className="font-medium">{job.estimated_time_minutes} minutes</span>
          </p>
        </div>
      )}
    </div>
  );
}

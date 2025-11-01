import { useEffect, useState } from 'react';
import { Users, Mic2, Globe, Loader2 } from 'lucide-react';
import { apiClient } from './api';
import type { SpeakerAnalysis } from './types';

interface SpeakerDisplayProps {
  jobId: string | null;
}

export function SpeakerDisplay({ jobId }: SpeakerDisplayProps) {
  const [analysis, setAnalysis] = useState<SpeakerAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) {
      setAnalysis(null);
      return;
    }

    const fetchSpeakerAnalysis = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await apiClient.getSpeakerAnalysis(jobId);
        setAnalysis(data);
      } catch (err) {
        console.error('Failed to fetch speaker analysis:', err);
        setError('Failed to load speaker information');
      } finally {
        setLoading(false);
      }
    };

    // Fetch immediately
    fetchSpeakerAnalysis();

    // Poll every 3 seconds if status is pending
    const interval = setInterval(() => {
      if (analysis?.status === 'pending') {
        fetchSpeakerAnalysis();
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [jobId]);

  if (!jobId) {
    return null;
  }

  if (loading && !analysis) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-center space-x-3">
          <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
          <p className="text-gray-600">Analyzing speakers...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  if (!analysis) {
    return null;
  }

  if (analysis.status === 'pending') {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-center space-x-3">
          <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
          <div>
            <p className="font-medium text-blue-900">Processing audio...</p>
            <p className="text-sm text-blue-600">{analysis.message}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
        <Users className="w-5 h-5" />
        <span>Speaker Analysis</span>
      </h3>

      <div className="space-y-4">
        {/* Language Detection */}
        {analysis.detected_language && (
          <div className="flex items-start space-x-3 p-3 bg-green-50 rounded-lg">
            <Globe className="w-5 h-5 text-green-600 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-gray-900">Detected Language</p>
              <p className="text-sm text-gray-700">
                {analysis.detected_language}
                {analysis.language_confidence && (
                  <span className="text-gray-500 ml-2">
                    ({Math.round(analysis.language_confidence * 100)}% confidence)
                  </span>
                )}
              </p>
            </div>
          </div>
        )}

        {/* Speaker Count */}
        <div className="flex items-start space-x-3 p-3 bg-purple-50 rounded-lg">
          <Users className="w-5 h-5 text-purple-600 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-gray-900">Detected Speakers</p>
            <p className="text-sm text-gray-700">
              {analysis.total_speakers || 1} {analysis.total_speakers === 1 ? 'speaker' : 'speakers'} identified
            </p>
          </div>
        </div>

        {/* Voice Assignments */}
        {analysis.voice_assignments && Object.keys(analysis.voice_assignments).length > 0 && (
          <div className="border-t pt-4">
            <p className="text-sm font-medium text-gray-900 mb-3 flex items-center space-x-2">
              <Mic2 className="w-4 h-4" />
              <span>Voice Assignments</span>
            </p>
            <div className="space-y-2">
              {Object.entries(analysis.voice_assignments).map(([speaker, voice]) => (
                <div
                  key={speaker}
                  className="flex items-center justify-between p-2 bg-gray-50 rounded"
                >
                  <span className="text-sm text-gray-700">{speaker}</span>
                  <span className="text-sm font-medium text-blue-600">{voice}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="mt-4 p-3 bg-blue-50 rounded-lg">
          <p className="text-xs text-gray-600">
            ✨ Voices are automatically assigned based on speaker characteristics and detected emotions
          </p>
        </div>
      </div>
    </div>
  );
}

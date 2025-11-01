import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload as UploadIcon, Loader2 } from 'lucide-react';
import { Layout } from './Layout';
import { VideoUpload } from './VideoUpload';
import { LanguageSelector } from './LanguageSelector';
import { VoiceConfigurator } from './VoiceConfigurator';
import { useDubbingStore } from './store';
import { apiClient } from './api';

export function UploadPage() {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    sourceLanguage,
    targetLanguage,
    primaryVoice,
    secondaryVoice,
    setSourceLanguage,
    setTargetLanguage,
    setPrimaryVoice,
    setSecondaryVoice,
    setJobId,
  } = useDubbingStore();

  const handleClearFile = () => {
    setSelectedFile(null);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please select a video file');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const job = await apiClient.uploadVideo(
        selectedFile,
        sourceLanguage,
        targetLanguage,
        primaryVoice,
        secondaryVoice || undefined,
        setUploadProgress
      );

      setJobId(job.job_id);
      navigate(`/jobs/${job.job_id}`);
    } catch (err) {
      console.error('Upload failed:', err);
      setError(err instanceof Error ? err.message : 'Failed to upload video');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Video for Dubbing</h1>
          <p className="text-gray-600">
            Upload your video and configure dubbing settings to get started
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Video File</h2>
            <VideoUpload
              onFileSelect={setSelectedFile}
              selectedFile={selectedFile}
              onClear={handleClearFile}
              disabled={isUploading}
            />
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Language Settings</h2>
            <LanguageSelector
              sourceLanguage={sourceLanguage}
              targetLanguage={targetLanguage}
              onSourceChange={setSourceLanguage}
              onTargetChange={setTargetLanguage}
              disabled={isUploading}
            />
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Voice Configuration</h2>
            <VoiceConfigurator
              primaryVoice={primaryVoice}
              secondaryVoice={secondaryVoice}
              onPrimaryVoiceChange={setPrimaryVoice}
              onSecondaryVoiceChange={setSecondaryVoice}
              disabled={isUploading}
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-600">{error}</p>
            </div>
          )}

          {isUploading && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center space-x-3 mb-2">
                <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                <p className="text-blue-600 font-medium">Uploading video...</p>
              </div>
              <div className="w-full bg-blue-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-sm text-blue-600 mt-1">{uploadProgress}%</p>
            </div>
          )}

          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={() => navigate('/')}
              disabled={isUploading}
              className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!selectedFile || isUploading}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Uploading...</span>
                </>
              ) : (
                <>
                  <UploadIcon className="w-5 h-5" />
                  <span>Start Dubbing</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </Layout>
  );
}

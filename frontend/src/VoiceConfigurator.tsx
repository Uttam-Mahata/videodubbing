import { useState, useEffect } from 'react';
import { Volume2 } from 'lucide-react';
import { apiClient } from './api';
import type { VoiceOption } from './types';

interface VoiceConfiguratorProps {
  primaryVoice: string;
  secondaryVoice: string | null;
  onPrimaryVoiceChange: (voice: string) => void;
  onSecondaryVoiceChange: (voice: string | null) => void;
  disabled?: boolean;
}

export function VoiceConfigurator({
  primaryVoice,
  secondaryVoice,
  onPrimaryVoiceChange,
  onSecondaryVoiceChange,
  disabled,
}: VoiceConfiguratorProps) {
  const [voices, setVoices] = useState<VoiceOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [showSecondary, setShowSecondary] = useState(false);

  useEffect(() => {
    const fetchVoices = async () => {
      try {
        const voiceList = await apiClient.getVoices();
        setVoices(voiceList);
      } catch (error) {
        console.error('Failed to fetch voices:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchVoices();
  }, []);

  const handleAddSecondaryVoice = () => {
    setShowSecondary(true);
    if (voices.length > 0) {
      onSecondaryVoiceChange(voices[0].name);
    }
  };

  const handleRemoveSecondaryVoice = () => {
    setShowSecondary(false);
    onSecondaryVoiceChange(null);
  };

  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="primary-voice" className="block text-sm font-medium text-gray-700 mb-2">
          Primary Voice
        </label>
        <div className="flex items-center space-x-3">
          <Volume2 className="w-5 h-5 text-gray-400" />
          <select
            id="primary-voice"
            value={primaryVoice}
            onChange={(e) => onPrimaryVoiceChange(e.target.value)}
            disabled={disabled || loading}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
          >
            {loading ? (
              <option>Loading voices...</option>
            ) : (
              voices.map((voice) => (
                <option key={voice.name} value={voice.name}>
                  {voice.name} ({voice.style})
                </option>
              ))
            )}
          </select>
        </div>
      </div>

      {showSecondary ? (
        <div>
          <label htmlFor="secondary-voice" className="block text-sm font-medium text-gray-700 mb-2">
            Secondary Voice (Optional)
          </label>
          <div className="flex items-center space-x-3">
            <Volume2 className="w-5 h-5 text-gray-400" />
            <select
              id="secondary-voice"
              value={secondaryVoice || ''}
              onChange={(e) => onSecondaryVoiceChange(e.target.value || null)}
              disabled={disabled || loading}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
            >
              {loading ? (
                <option>Loading voices...</option>
              ) : (
                voices.map((voice) => (
                  <option key={voice.name} value={voice.name}>
                    {voice.name} ({voice.style})
                  </option>
                ))
              )}
            </select>
            <button
              onClick={handleRemoveSecondaryVoice}
              disabled={disabled}
              className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
            >
              Remove
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={handleAddSecondaryVoice}
          disabled={disabled || loading}
          className="px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50"
        >
          Add Secondary Voice
        </button>
      )}
    </div>
  );
}

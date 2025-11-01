import { Sparkles, Info } from 'lucide-react';

interface VoiceConfiguratorProps {
  disabled?: boolean;
}

export function VoiceConfigurator({ disabled }: VoiceConfiguratorProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-start space-x-3 p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200">
        <Sparkles className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <h4 className="font-medium text-gray-900 mb-2">AI-Powered Voice Selection</h4>
          <p className="text-sm text-gray-700 mb-3">
            Our intelligent system will automatically:
          </p>
          <ul className="text-sm text-gray-700 space-y-1.5">
            <li className="flex items-start">
              <span className="text-purple-600 mr-2">•</span>
              <span>Detect all speakers in your video</span>
            </li>
            <li className="flex items-start">
              <span className="text-purple-600 mr-2">•</span>
              <span>Analyze emotional tone and speaking style</span>
            </li>
            <li className="flex items-start">
              <span className="text-purple-600 mr-2">•</span>
              <span>Assign appropriate voices from our library of 30+ options</span>
            </li>
            <li className="flex items-start">
              <span className="text-purple-600 mr-2">•</span>
              <span>Match emotions in the dubbed audio (cheerful, serious, excited, etc.)</span>
            </li>
          </ul>
        </div>
      </div>

      <div className="flex items-start space-x-3 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
        <div>
          <p className="text-sm text-gray-700">
            After uploading, you'll see detailed speaker analysis including the number of speakers detected,
            assigned voices, and detected emotions. The system uses advanced AI to ensure natural-sounding
            dubbed audio that preserves the original emotional expression.
          </p>
        </div>
      </div>

      {disabled && (
        <div className="text-center py-2">
          <p className="text-sm text-gray-500">Voice assignment will begin after upload</p>
        </div>
      )}
    </div>
  );
}

import { useState, useEffect } from 'react';
import { ArrowLeftRight } from 'lucide-react';
import { apiClient } from './api';
import type { Language } from './types';

interface LanguageSelectorProps {
  sourceLanguage: string;
  targetLanguage: string;
  onSourceChange: (lang: string) => void;
  onTargetChange: (lang: string) => void;
  disabled?: boolean;
}

export function LanguageSelector({
  sourceLanguage,
  targetLanguage,
  onSourceChange,
  onTargetChange,
  disabled,
}: LanguageSelectorProps) {
  const [languages, setLanguages] = useState<Language[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLanguages = async () => {
      try {
        const response = await apiClient.getLanguages();
        setLanguages(response.languages);
      } catch (error) {
        console.error('Failed to fetch languages:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchLanguages();
  }, []);

  const handleSwap = () => {
    if (!disabled) {
      const temp = sourceLanguage;
      onSourceChange(targetLanguage);
      onTargetChange(temp);
    }
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
        <div>
          <label htmlFor="source-language" className="block text-sm font-medium text-gray-700 mb-2">
            Source Language
          </label>
          <select
            id="source-language"
            value={sourceLanguage}
            onChange={(e) => onSourceChange(e.target.value)}
            disabled={disabled || loading}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
          >
            {loading ? (
              <option>Loading...</option>
            ) : (
              <>
                <option value="auto">🤖 Auto-Detect (Recommended)</option>
                {languages.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.name}
                  </option>
                ))}
              </>
            )}
          </select>
          <p className="mt-1 text-xs text-gray-500">
            {sourceLanguage === 'auto' ? 'AI will detect the language automatically' : 'Manually selected'}
          </p>
        </div>

        <div className="flex justify-center md:mt-8">
          <button
            onClick={handleSwap}
            disabled={disabled || loading}
            className="p-3 bg-gray-100 hover:bg-gray-200 rounded-full transition-colors disabled:opacity-50"
            aria-label="Swap languages"
          >
            <ArrowLeftRight className="w-5 h-5 text-gray-700" />
          </button>
        </div>

        <div className="md:col-start-2">
          <label htmlFor="target-language" className="block text-sm font-medium text-gray-700 mb-2">
            Target Language
          </label>
          <select
            id="target-language"
            value={targetLanguage}
            onChange={(e) => onTargetChange(e.target.value)}
            disabled={disabled || loading}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
          >
            {loading ? (
              <option>Loading...</option>
            ) : (
              languages.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.name}
                </option>
              ))
            )}
          </select>
        </div>
      </div>
    </div>
  );
}

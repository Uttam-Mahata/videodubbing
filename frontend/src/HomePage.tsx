import { useNavigate } from 'react-router-dom';
import { Upload, List, Globe, Volume2, Zap, Shield } from 'lucide-react';

export function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Video Dubbing Platform
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Transform your videos into multiple languages with AI-powered dubbing
          </p>
          <div className="flex items-center justify-center space-x-4">
            <button
              onClick={() => navigate('/upload')}
              className="flex items-center space-x-2 px-8 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-lg font-semibold shadow-lg hover:shadow-xl"
            >
              <Upload className="w-6 h-6" />
              <span>Start Dubbing</span>
            </button>
            <button
              onClick={() => navigate('/jobs')}
              className="flex items-center space-x-2 px-8 py-4 bg-white border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-lg font-semibold shadow-lg hover:shadow-xl"
            >
              <List className="w-6 h-6" />
              <span>View Jobs</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          <div className="bg-white rounded-xl shadow-lg p-8 hover:shadow-xl transition-shadow">
            <div className="w-14 h-14 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <Globe className="w-8 h-8 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">24 Languages</h3>
            <p className="text-gray-600">
              Support for major global languages including English, Spanish, French, German, Japanese, and more
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-8 hover:shadow-xl transition-shadow">
            <div className="w-14 h-14 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <Volume2 className="w-8 h-8 text-purple-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">30 Voice Options</h3>
            <p className="text-gray-600">
              Choose from a diverse range of AI voices with different styles and characteristics
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-8 hover:shadow-xl transition-shadow">
            <div className="w-14 h-14 bg-green-100 rounded-lg flex items-center justify-center mb-4">
              <Zap className="w-8 h-8 text-green-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Fast Processing</h3>
            <p className="text-gray-600">
              Powered by Google Gemini AI for accurate transcription, translation, and synthesis
            </p>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-12 mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
                1
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Upload Video</h3>
              <p className="text-gray-600 text-sm">Upload your video file and select source language</p>
            </div>

            <div className="text-center">
              <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
                2
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Configure Settings</h3>
              <p className="text-gray-600 text-sm">Choose target language and voice preferences</p>
            </div>

            <div className="text-center">
              <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
                3
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">AI Processing</h3>
              <p className="text-gray-600 text-sm">Our AI transcribes, translates, and generates speech</p>
            </div>

            <div className="text-center">
              <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
                4
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Download Result</h3>
              <p className="text-gray-600 text-sm">Get your dubbed video with natural-sounding audio</p>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl shadow-lg p-12 text-center text-white">
          <Shield className="w-16 h-16 mx-auto mb-4" />
          <h2 className="text-3xl font-bold mb-4">Production-Ready Platform</h2>
          <p className="text-lg text-blue-100 mb-8 max-w-2xl mx-auto">
            Built with FastAPI, React, and Google ADK for reliable, scalable video dubbing at enterprise quality
          </p>
          <button
            onClick={() => navigate('/upload')}
            className="px-8 py-4 bg-white text-blue-600 rounded-lg hover:bg-blue-50 transition-colors text-lg font-semibold shadow-lg"
          >
            Get Started Now
          </button>
        </div>
      </div>
    </div>
  );
}

# Video Dubbing Application - Quick Start Guide

This guide will help you get the Video Dubbing application up and running quickly.

## Prerequisites

- **Python 3.12+** with pip
- **Node.js 18+** with npm
- **MongoDB** (local or cloud)
- **Redis** (local or cloud)
- **Google Gemini API Key** ([Get it here](https://ai.google.dev/))
- **Google Cloud Storage** (optional, for production)

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/Uttam-Mahata/videodubbing.git
cd videodubbing
```

### 2. Backend Setup

#### Install Python Dependencies

```bash
pip install -e .
```

Or if you prefer using a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

#### Configure Environment Variables

```bash
cd backend
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Required
GEMINI_API_KEY=your-gemini-api-key-here
SECRET_KEY=your-secret-key-change-in-production

# Optional (defaults work for local development)
MONGODB_URL=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

#### Start Required Services

**Option 1: Using Docker Compose (Recommended)**
```bash
# Start MongoDB and Redis
docker-compose up -d

# Verify services are running
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Option 2: Native Installation**

**MongoDB** (if not running):
```bash
# macOS (using Homebrew)
brew services start mongodb-community

# Linux (using systemd)
sudo systemctl start mongod

# Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

**Redis** (if not running):
```bash
# macOS (using Homebrew)
brew services start redis

# Linux (using systemd)
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 --name redis redis:latest
```

#### Run Backend Server

```bash
cd backend
python main.py
```

Or using uvicorn directly:
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`
API docs at: `http://localhost:8000/api/docs`

### 3. Frontend Setup

#### Install Dependencies

```bash
cd frontend
npm install
```

#### Configure Environment Variables

```bash
cp .env.example .env
```

The default values should work for local development:
```bash
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
VITE_MAX_FILE_SIZE=524288000
```

#### Run Frontend Development Server

```bash
npm run dev
```

Frontend will be available at: `http://localhost:5173`

## Using the Application

### 1. Access the Application

Open your browser and navigate to `http://localhost:5173`

### 2. Upload a Video

1. Click "Start Dubbing" or navigate to `/upload`
2. Drag and drop a video file or click to browse
3. Select source language (e.g., English)
4. Select target language (e.g., Spanish)
5. Choose a voice from the dropdown (e.g., Kore)
6. Click "Start Dubbing"

### 3. Monitor Progress

- You'll be redirected to the job detail page
- Watch real-time progress through 9 processing stages
- See estimated time remaining

### 4. Download Result

- Once processing is complete, click "Download"
- Your dubbed video will be downloaded with a 24-hour valid URL

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### List Languages
```bash
curl http://localhost:8000/api/v1/languages
```

### List Voices
```bash
curl http://localhost:8000/api/v1/voices
```

### Create Job
```bash
curl -X POST http://localhost:8000/api/v1/jobs/create \
  -F "video=@/path/to/video.mp4" \
  -F "source_language=en-US" \
  -F "target_language=es-US" \
  -F "primary_voice=Kore"
```

### Get Job Status
```bash
curl http://localhost:8000/api/v1/jobs/{job_id}
```

### List Jobs
```bash
curl http://localhost:8000/api/v1/jobs?user_id=default_user
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  Frontend (React)                    │
│  - Video Upload                                      │
│  - Language & Voice Selection                        │
│  - Progress Tracking                                 │
│  - Job Management                                    │
└─────────────────────────────────────────────────────┘
                         ▼ ▲
                    REST / WebSocket
                         ▼ ▲
┌─────────────────────────────────────────────────────┐
│                  Backend (FastAPI)                   │
│  - API Endpoints                                     │
│  - Google ADK Agent Orchestration                    │
│  - Job Management                                    │
└─────────────────────────────────────────────────────┘
                         ▼ ▲
┌─────────────────────────────────────────────────────┐
│              Google Gemini API                       │
│  - Audio Understanding (Transcription)               │
│  - Translation (LLM)                                 │
│  - Speech Synthesis (TTS)                            │
└─────────────────────────────────────────────────────┘
```

## Processing Pipeline

1. **Intake**: Video upload and validation
2. **Audio Extraction**: Extract audio track from video
3. **Transcription**: Convert speech to text with timestamps
4. **Translation**: Translate text to target language
5. **Speech Synthesis**: Generate dubbed audio with selected voice
6. **Timing Sync**: Match timing and pace of original
7. **Audio Merging**: Combine dubbed audio with video
8. **Quality Assurance**: Validate output quality
9. **Delivery**: Generate download URL

## Troubleshooting

### Backend Won't Start

**MongoDB Connection Failed**
```bash
# Check if MongoDB is running
mongosh --eval "db.version()"

# If not installed, install MongoDB:
# macOS: brew install mongodb-community
# Ubuntu: sudo apt install mongodb
# Docker: docker run -d -p 27017:27017 mongo:latest
```

**Redis Connection Failed**
```bash
# Check if Redis is running
redis-cli ping

# If not installed, install Redis:
# macOS: brew install redis
# Ubuntu: sudo apt install redis-server
# Docker: docker run -d -p 6379:6379 redis:latest
```

**Import Error: google-adk**
```bash
# Reinstall dependencies
pip install --upgrade google-adk google-genai
```

### Frontend Won't Start

**Module Not Found**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Vite Build Error**
```bash
# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

### API Connection Issues

**CORS Error**
- Check `CORS_ORIGINS` in backend `.env`
- Ensure it includes `http://localhost:5173`

**Network Error**
- Verify backend is running on port 8000
- Check `VITE_API_URL` in frontend `.env`

### Upload Fails

**File Too Large**
- Default max size is 500MB
- Adjust `VITE_MAX_FILE_SIZE` in frontend `.env`
- Adjust `max_upload_size_mb` in backend settings

**Invalid File Format**
- Supported formats: MP4, AVI, MOV, MKV, WebM
- Ensure file has valid video codec

## Development Tips

### Backend Development

```bash
# Run with auto-reload
uvicorn backend.main:app --reload

# Run tests (when available)
pytest

# Check code style
ruff check .
black --check .

# Type checking
mypy backend/
```

### Frontend Development

```bash
# Run dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Production Deployment

### Backend

1. Set environment variables in production
2. Use production MongoDB and Redis
3. Configure Google Cloud Storage
4. Set `DEBUG=false` and `ENVIRONMENT=production`
5. Use HTTPS for API endpoints
6. Set up proper authentication
7. Configure rate limiting
8. Enable monitoring and logging

### Frontend

1. Build production bundle: `npm run build`
2. Set production API URL in `.env`
3. Deploy `dist` folder to CDN/static hosting
4. Configure HTTPS
5. Enable caching headers
6. Set up error tracking (Sentry, etc.)

### Recommended Stack

- **Backend**: Google Cloud Run, AWS ECS, or Kubernetes
- **Frontend**: Vercel, Netlify, or Cloudflare Pages
- **Database**: MongoDB Atlas
- **Cache**: Redis Cloud or AWS ElastiCache
- **Storage**: Google Cloud Storage
- **Monitoring**: Datadog, New Relic, or Prometheus

## Next Steps

1. Read the [full README](./README.md) for architecture details
2. Check [Frontend Documentation](./frontend/README_FRONTEND.md)
3. Review [Backend Documentation](./backend/README.md)
4. Explore [Google ADK Documentation](https://google.github.io/adk-docs/)
5. Check [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)

## Support

For issues and questions:
- GitHub Issues: https://github.com/Uttam-Mahata/videodubbing/issues
- Documentation: See README files in each directory

## License

See LICENSE file in the repository root.

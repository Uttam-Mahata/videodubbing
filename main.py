"""
Video Dubbing Application
Main entry point for the application
"""

from backend.main import app

def main():
    """
    Main entry point
    
    For development, run: uvicorn backend.main:app --reload
    For production, see backend/README.md for deployment instructions
    """
    print("Video Dubbing Application")
    print("=" * 50)
    print("Backend: FastAPI with Google ADK and Gemini APIs")
    print("Frontend: React + Vite")
    print()
    print("To start the backend:")
    print("  cd backend && python main.py")
    print()
    print("To start the frontend:")
    print("  cd frontend && npm run dev")
    print()
    print("API Documentation: http://localhost:8000/api/docs")


if __name__ == "__main__":
    main()

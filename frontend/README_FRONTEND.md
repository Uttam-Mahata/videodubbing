# Video Dubbing Frontend

Production-ready frontend application for the Video Dubbing platform, built with React 19, TypeScript, and Vite.

## Features

- **Video Upload**: Drag-and-drop interface with file validation
- **Language Selection**: Support for 24+ languages with swap functionality
- **Voice Configuration**: Choose from 30+ AI voices with different styles
- **Real-time Progress**: WebSocket integration for live job status updates
- **Job Management**: View, track, and manage all dubbing jobs
- **Responsive Design**: Mobile-first approach with TailwindCSS
- **Error Handling**: Comprehensive error boundaries and user feedback
- **Production Ready**: Optimized build with code splitting and lazy loading

## Tech Stack

- **React 19.1.1** - Latest React with hooks
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool (rolldown-vite fork)
- **TailwindCSS 4** - Modern utility-first CSS
- **React Router 7** - Client-side routing
- **Zustand** - Lightweight state management
- **React Query** - Server state management
- **Axios** - HTTP client
- **Lucide React** - Icon library

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
VITE_MAX_FILE_SIZE=524288000
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Build

```bash
npm run build
```

Build artifacts will be in the `dist` directory.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── api.ts                 # API client with axios
│   ├── store.ts               # Zustand store
│   ├── types.ts               # TypeScript types
│   ├── useJobProgress.ts      # WebSocket hook
│   ├── ErrorBoundary.tsx      # Error boundary component
│   ├── VideoUpload.tsx        # Video upload component
│   ├── LanguageSelector.tsx   # Language selection component
│   ├── VoiceConfigurator.tsx  # Voice configuration component
│   ├── ProgressTracker.tsx    # Progress display component
│   ├── JobCard.tsx            # Job card component
│   ├── HomePage.tsx           # Home page
│   ├── UploadPage.tsx         # Upload page
│   ├── JobDetailPage.tsx      # Job detail page
│   ├── JobListPage.tsx        # Job list page
│   ├── App.tsx                # Main app component
│   ├── main.tsx               # Entry point
│   └── index.css              # Global styles
├── .env.example               # Environment variables template
├── package.json               # Dependencies
├── tsconfig.json              # TypeScript config
├── vite.config.ts             # Vite config
└── tailwind.config.js         # TailwindCSS config (if exists)
```

## Key Components

### VideoUpload
- Drag-and-drop file upload
- File validation (size, format)
- Progress indication
- Clear file functionality

### LanguageSelector
- Dropdown for source and target languages
- Swap languages button
- Fetches language list from API

### VoiceConfigurator
- Primary voice selection
- Optional secondary voice
- Fetches available voices from API

### ProgressTracker
- Real-time progress visualization
- 9-stage pipeline display
- Estimated time remaining
- Status indicators with icons

### JobCard
- Job summary with status
- Progress bar
- Quick actions (download, view details)
- Formatted timestamps

## API Integration

All API calls are handled through the `apiClient` in `src/api.ts`:

- `uploadVideo()` - Upload video with multipart/form-data
- `getJob()` - Fetch job details
- `listJobs()` - List user jobs with pagination
- `downloadVideo()` - Get signed download URL
- `cancelJob()` - Cancel processing job
- `retryJob()` - Retry failed job
- `getVoices()` - Fetch available voices
- `getLanguages()` - Fetch supported languages

## WebSocket Integration

Real-time job progress updates via WebSocket:

```typescript
const { progress, error, isConnected } = useJobProgress(jobId);
```

WebSocket endpoint: `ws://localhost:8000/ws/jobs/{jobId}`

## State Management

### Zustand Store
Global state for dubbing configuration:
- Current job ID
- Upload progress
- Language selection
- Voice configuration

### React Query
Server state management:
- Automatic caching
- Background refetching
- Error handling
- Loading states

## Styling

### TailwindCSS
Utility-first CSS framework with custom configuration:
- Responsive breakpoints
- Custom color palette
- Component classes
- Dark mode support (optional)

### Design System
- Primary color: Blue (#3B82F6)
- Success: Green (#10B981)
- Error: Red (#EF4444)
- Warning: Yellow (#F59E0B)
- Gray scale for text and backgrounds

## Error Handling

### Error Boundary
Catches React errors and displays user-friendly fallback UI.

### API Errors
- Network errors with retry
- Validation errors with user feedback
- Server errors with detailed messages

### Loading States
- Skeleton loaders
- Spinners for async operations
- Progress bars for uploads

## Accessibility

- ARIA labels for all interactive elements
- Keyboard navigation support
- Focus indicators
- Screen reader friendly
- Semantic HTML

## Performance Optimization

- Code splitting by route
- Lazy loading of components
- Image optimization
- Memoization of expensive computations
- Virtual scrolling for large lists (optional)

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Development Guidelines

1. Use TypeScript for type safety
2. Follow React hooks best practices
3. Keep components small and focused
4. Use TailwindCSS utility classes
5. Handle errors gracefully
6. Add loading states for async operations
7. Test responsive design on multiple devices
8. Use semantic HTML
9. Add proper ARIA attributes
10. Optimize bundle size

## Deployment

### Build for Production

```bash
npm run build
```

### Serve with Static Server

```bash
npm install -g serve
serve -s dist -p 3000
```

### Environment Variables in Production

Ensure environment variables are set:
- `VITE_API_URL` - Production API URL
- `VITE_WS_URL` - Production WebSocket URL

## Troubleshooting

### API Connection Issues
- Check if backend is running
- Verify `VITE_API_URL` is correct
- Check CORS settings on backend

### Build Errors
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Clear Vite cache: `rm -rf node_modules/.vite`

### WebSocket Not Connecting
- Verify WebSocket endpoint
- Check browser console for errors
- Ensure backend WebSocket server is running

## Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Submit pull request

## License

This project is part of the Video Dubbing Application.

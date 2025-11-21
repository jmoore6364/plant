# Web Dashboard UI

The Plant AI System Health Analyzer includes a modern React-based web dashboard for real-time monitoring and analysis.

## Overview

**Technology Stack:**
- React 18 + TypeScript
- Vite (lightning-fast build tool)
- TailwindCSS (utility-first styling)
- React Router (client-side routing)
- TanStack Query (data fetching & caching)
- Recharts (charts and visualizations)
- Lucide React (beautiful icons)
- Axios (HTTP client)

## Features

### 🎯 Dashboard (`/`)
The main dashboard provides a comprehensive overview of system health:

- **Real-time Metrics Cards**
  - CPU Usage (with color-coded status)
  - Memory Usage
  - Disk Usage
  - Process Count
  - Auto-refreshes every 5 seconds

- **Live Charts**
  - CPU & Memory trends over time
  - Disk usage trends
  - Historical data visualization
  - Interactive tooltips

- **Alert Notifications**
  - Critical resource warnings
  - Issue count and details
  - Visual indicators (red/yellow/green)

### 📝 Logs (`/logs`)
Log analysis and processing interface:

- **Log Upload**
  - Paste log content directly
  - Trigger AI-powered analysis

- **Analysis Results**
  - Error pattern detection
  - Anomaly identification
  - AI-generated insights

- **Configuration Options**
  - Enable/disable AI analysis
  - Auto-fix generation toggle
  - Auto-PR creation toggle

### 📊 Metrics (`/metrics`)
Detailed system metrics view:

- CPU statistics
- Memory breakdown
- Disk space information
- Network activity
- Process information
- Auto-refreshes every 5 seconds

### 🔧 Fixes & PRs (`/fixes`)
Track generated fixes and pull requests:

- Fix history with status
- PR tracking (open/merged/closed)
- Severity indicators
- GitHub integration
- Timestamps and metadata

## Setup & Installation

### Prerequisites

```bash
# Node.js 18+ and npm
node --version  # Should be 18.x or higher
npm --version   # Should be 9.x or higher
```

### Installation

```bash
# Navigate to UI directory
cd src/ui

# Install dependencies
npm install
```

### Development

```bash
# Start development server (with hot reload)
npm run dev

# The UI will be available at:
# http://localhost:5173
```

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

### Linting

```bash
# Run ESLint
npm run lint
```

## Configuration

### API Endpoint

The UI connects to the FastAPI backend. The API URL is configured in each page:

```typescript
const API_URL = 'http://localhost:8000';
```

To change the API endpoint for production, update this constant in:
- `src/ui/src/pages/Dashboard.tsx`
- `src/ui/src/pages/Logs.tsx`
- `src/ui/src/pages/Metrics.tsx`

Or better yet, use environment variables:

```typescript
// src/ui/src/config.ts
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

Then create `.env` file:
```bash
VITE_API_URL=https://your-api-domain.com
```

## Full Stack Development

### Option 1: Manual Start

```bash
# Terminal 1: Start API Server
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start UI Development Server
cd src/ui
npm run dev
```

### Option 2: Docker Compose

```bash
# Start entire stack (includes UI, API, database, Redis, etc.)
docker-compose up -d
```

## Project Structure

```
src/ui/
├── package.json          # Dependencies and scripts
├── src/
│   ├── App.tsx          # Main app component with routing
│   └── pages/
│       ├── Dashboard.tsx # Main dashboard
│       ├── Logs.tsx     # Log analysis
│       ├── Metrics.tsx  # Detailed metrics
│       └── Fixes.tsx    # Fixes and PRs
```

## API Endpoints Used

The UI interacts with these backend endpoints:

### Dashboard
- `GET /metrics/current` - Current system metrics
- `GET /metrics/issues` - Resource issues/alerts
- `GET /metrics/history?limit=50` - Historical metrics

### Logs
- `POST /analyze` - Analyze log content
  ```json
  {
    "log_content": "...",
    "include_ai_analysis": true,
    "auto_fix": false,
    "auto_pr": false
  }
  ```

### Metrics
- `GET /metrics/detailed` - Detailed system metrics

### Fixes
- `GET /fixes/recent` - Recent fixes
- `GET /prs/recent` - Recent pull requests

## Styling

The UI uses TailwindCSS for styling. Key design principles:

- **Responsive**: Works on desktop, tablet, and mobile
- **Color-coded status**: Green (good), Yellow (warning), Red (critical)
- **Clean & Modern**: Minimalist design with good spacing
- **Accessible**: ARIA labels and semantic HTML

### Color Scheme

```css
/* Status Colors */
.status-good: bg-green-100 text-green-600
.status-warning: bg-yellow-100 text-yellow-600
.status-critical: bg-red-100 text-red-600
.status-info: bg-blue-100 text-blue-600

/* Primary */
.primary: text-blue-600
.bg-primary: bg-blue-600
```

## Auto-Refresh Behavior

- **Dashboard metrics**: Refresh every 5 seconds
- **Dashboard history**: Refresh every 10 seconds
- **Detailed metrics**: Refresh every 5 seconds

Customize refresh intervals in the `useQuery` hooks:

```typescript
const { data } = useQuery({
  queryKey: ['current-metrics'],
  queryFn: async () => { /* ... */ },
  refetchInterval: 5000, // Change this value (milliseconds)
});
```

## Troubleshooting

### CORS Errors

If you see CORS errors in the browser console:

```bash
# The FastAPI backend needs CORS enabled
# Check src/api/main.py for CORS middleware configuration
```

### Connection Refused

```bash
# Ensure the API server is running
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Check the API_URL in UI pages matches your backend URL
```

### Build Errors

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

### Port Already in Use

```bash
# Vite default port is 5173
# If it's in use, Vite will automatically try 5174, 5175, etc.

# Or specify a different port:
npm run dev -- --port 3000
```

## Performance

The UI is optimized for performance:

- **Code Splitting**: Automatic with React Router
- **React Query Caching**: Reduces redundant API calls
- **Lazy Loading**: Charts load on demand
- **Optimized Bundle**: Vite creates small, optimized bundles

### Build Size

```bash
# Check bundle size
npm run build

# Typical sizes:
# - Gzipped JS: ~150KB
# - CSS: ~10KB
```

## Browser Support

- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)

## Future Enhancements

Potential improvements for the UI:

- [ ] Dark mode toggle
- [ ] User authentication UI
- [ ] Advanced filtering options
- [ ] Export data as CSV/JSON
- [ ] Customizable dashboard widgets
- [ ] Notification settings page
- [ ] Real-time WebSocket updates
- [ ] Mobile app (React Native)

## Contributing

When contributing to the UI:

1. Follow React best practices
2. Use TypeScript for type safety
3. Keep components small and focused
4. Add proper error handling
5. Test on multiple browsers
6. Ensure responsive design

## Related Documentation

- [Quick Start Guide](QUICKSTART.md)
- [API Documentation](API.md)
- [Development Guide](DEVELOPMENT.md)
- [Deployment Guide](DEPLOYMENT.md)

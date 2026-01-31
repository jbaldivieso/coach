# Coach

A weightlifting session tracking Progressive Web App (PWA) with a Vue 3 frontend and Django backend.

## Project Structure

```
coach/
├── backend/           # Django backend
│   ├── accounts/      # User authentication app
│   ├── config/        # Django project settings
│   └── manage.py
├── frontend/          # Vue 3 frontend
│   ├── src/
│   │   ├── api/       # API client
│   │   ├── components/# Vue components
│   │   ├── router/    # Vue Router config
│   │   ├── stores/    # Pinia stores
│   │   ├── styles/    # SCSS styles (Bulma)
│   │   └── views/     # Page components
│   └── vite.config.ts
└── README.md
```

## Tech Stack

### Backend
- **Python 3.12** with **uv** for package management
- **Django 6.0** web framework
- **Django Ninja** for REST API
- **SQLite** database (dev and production)
- **pytest** + **pytest-django** for testing

### Frontend
- **Vue 3** with Composition API and TypeScript
- **Vite** build tool
- **Bulma** CSS framework with SASS
- **Pinia** for state management
- **Vue Router** for navigation
- **Vitest** for testing
- **PWA** support with `vite-plugin-pwa` (offline capability, installable, Wake Lock API)

## Development Setup

### Backend

```bash
cd backend

# Install dependencies
uv sync

# Run migrations
DJANGO_SETTINGS_MODULE=config.settings uv run python manage.py migrate

# Create a superuser (optional)
DJANGO_SETTINGS_MODULE=config.settings uv run python manage.py createsuperuser

# Run the development server
DJANGO_SETTINGS_MODULE=config.settings uv run python manage.py runserver
```

The backend runs on http://127.0.0.1:8000

### Frontend

**First time setup:**

```bash
cd frontend

# Install all npm dependencies (only needed once, or when dependencies change)
npm install
```

**Running the development server:**

```bash
cd frontend

# Start the dev server with hot reload
npm run dev
```

The frontend development server runs on http://localhost:5173

**Note:** The frontend proxies `/api` requests to the backend, so both servers need to be running during development.

#### Testing the Production Build Locally

To test the production PWA build locally:

```bash
cd frontend

# Build for production
npm run build

# Preview the production build
npm run preview
```

The production preview server runs on http://localhost:4173

**Important:** The production build uses `base: "/static/"` for Django static file serving. The preview server handles this correctly, but PWA features (service worker, offline support, installation) only work in the production build, not in development mode.

## Testing

### Backend Tests

```bash
cd backend
DJANGO_SETTINGS_MODULE=config.settings uv run pytest -v
```

### Frontend Tests

```bash
cd frontend
npm run test:run      # Run once
npm run test          # Watch mode
npm run test:coverage # With coverage
```

## API Endpoints

All API endpoints are prefixed with `/api/`.

### Health
- `GET /api/health/` - Health check

### Authentication
- `GET /api/accounts/csrf/` - Get CSRF token
- `POST /api/accounts/login/` - Login with username/password
- `POST /api/accounts/logout/` - Logout (requires auth)
- `GET /api/accounts/me/` - Get current user (requires auth)

### API Documentation

Django Ninja provides automatic OpenAPI documentation at:
- `GET /api/docs/` - Swagger UI

## Configuration

### Environment Variables

The backend supports these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | (insecure default) | Django secret key |
| `DJANGO_DEBUG` | `True` | Debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed hosts |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,...` | CORS origins |
| `CSRF_TRUSTED_ORIGINS` | `http://localhost:5173,...` | CSRF trusted origins |

**Important:** If `DJANGO_SETTINGS_MODULE` is set in your shell, you must override it or unset it when running Django commands.

### Session Duration

User sessions last 2 weeks and are refreshed on each request.

## Building for Production

### Frontend

```bash
cd frontend
npm run build
```

The built files will be in `frontend/dist/`.

### Backend

Collect static files:
```bash
cd backend
DJANGO_SETTINGS_MODULE=config.settings uv run python manage.py collectstatic
```

## Progressive Web App (PWA) Features

Coach is configured as a Progressive Web App with the following features:

- **Installable:** Can be installed on mobile devices (iOS, Android) and desktop browsers
- **Offline Support:** Service worker caches assets for offline functionality
- **Screen Wake Lock:** Keeps the screen awake during workouts (works best when installed as PWA on iOS)
- **App-like Experience:** Runs in standalone mode without browser UI when installed
- **Web App Manifest:** Custom icon, name, and theme color

### Installing on Mobile

**iOS (Safari):**
1. Visit the site in Safari
2. Tap the Share button
3. Scroll down and tap "Add to Home Screen"
4. Tap "Add"

**Android (Chrome):**
1. Visit the site in Chrome
2. Tap the menu (three dots)
3. Tap "Add to Home screen" or "Install app"
4. Confirm installation

### PWA Configuration Files

- `frontend/vite.config.ts` - PWA plugin configuration
- `frontend/public/icon.svg` - App icon (can be replaced with PNG icons)
- Service worker is auto-generated during build

**Note:** PWA features like service worker and installation prompts only work with the production build (`npm run build`), not in development mode.

## Architecture Notes for Future Development

### Adding New API Endpoints

1. Create or update an API router in the appropriate app (e.g., `backend/accounts/api.py`)
2. Register the router in `backend/config/api.py`
3. Write tests in the app's `tests.py`

### Adding New Frontend Pages

1. Create a view component in `frontend/src/views/`
2. Add the route in `frontend/src/router/index.ts`
3. Add navigation links if needed
4. Write tests in a `.spec.ts` file

### State Management

Use Pinia stores in `frontend/src/stores/` for global state. The `auth` store handles user authentication state.

### Styling

- Use Bulma CSS classes for layout and components
- Add custom styles in `frontend/src/styles/main.scss`
- The app is optimized for mobile-first, information-dense display

### API Communication

The `frontend/src/api/client.ts` provides a typed API client that:
- Handles CSRF tokens automatically
- Manages credentials/cookies
- Provides typed responses with error handling

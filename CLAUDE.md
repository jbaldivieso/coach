# Claude Code Instructions for Coach

This document provides instructions for AI agents working on this codebase.

## Project Overview

Coach is a weightlifting tracking PWA with:
- **Backend:** Django 6.0 + Django Ninja API (Python 3.12, uv)
- **Frontend:** Vue 3 + TypeScript + Vite + Bulma + PWA support

## Working Directory Context

Commands should be run from specific directories:
- Backend commands: `cd backend` first, prefix with `DJANGO_SETTINGS_MODULE=config.settings`
- Frontend commands: `cd frontend` first

## Common Tasks

### Running Tests

```bash
# Backend
cd backend && DJANGO_SETTINGS_MODULE=config.settings uv run pytest -v

# Frontend
cd frontend && npm run test:run
```

### Starting Development Servers

```bash
# Terminal 1 - Backend
cd backend && DJANGO_SETTINGS_MODULE=config.settings uv run python manage.py runserver

# Terminal 2 - Frontend (development)
cd frontend && npm run dev
```

### Building and Testing Production Frontend

```bash
# Build for production (outputs to frontend/dist)
cd frontend && npm run build

# Preview production build locally
cd frontend && npm run preview
```

**Note:** The production build uses `base: "/static/"` for Django static file serving. Use `npm run preview` (Vite's preview server) to test production builds locally - it handles the `/static/` base path correctly.

### Adding Python Dependencies

```bash
cd backend && uv add <package>     # runtime dependency
cd backend && uv add --dev <package>  # dev dependency
```

### Adding npm Dependencies

```bash
cd frontend && npm install <package>
cd frontend && npm install -D <package>  # dev dependency
```

## Code Patterns

### Backend API Endpoints

New API endpoints go in app-specific `api.py` files:

```python
# backend/<app>/api.py
from ninja import Router, Schema
from ninja.security import django_auth

router = Router()

class MySchema(Schema):
    field: str

@router.get("/endpoint/", response=MySchema, auth=django_auth)
def my_endpoint(request):
    return {"field": "value"}
```

Register routers in `backend/config/api.py`:

```python
from myapp.api import router as myapp_router
api.add_router("/myapp/", myapp_router, tags=["myapp"])
```

### Frontend Components

Use Vue 3 Composition API with `<script setup>`:

```vue
<script setup lang="ts">
import { ref, computed } from "vue";

const myRef = ref("");
const myComputed = computed(() => myRef.value.toUpperCase());
</script>

<template>
  <div class="container">
    <!-- Use Bulma classes -->
  </div>
</template>
```

### Frontend Stores (Pinia)

```typescript
// src/stores/mystore.ts
import { defineStore } from "pinia";
import { ref, computed } from "vue";

export const useMyStore = defineStore("mystore", () => {
  const data = ref<MyType | null>(null);
  const isLoaded = computed(() => data.value !== null);

  async function fetchData() {
    // ...
  }

  return { data, isLoaded, fetchData };
});
```

### API Calls from Frontend

Use the API client in `src/api/client.ts`:

```typescript
import { api } from "@/api/client";

const response = await api.get<MyType>("/api/endpoint/");
if (response.data) {
  // success
} else {
  // error: response.error
}
```

## Important Notes

1. **DJANGO_SETTINGS_MODULE:** The environment has `DJANGO_SETTINGS_MODULE=settings.local` set. Always override with `DJANGO_SETTINGS_MODULE=config.settings` for Django commands.

2. **Session Auth:** The app uses Django session authentication (not JWT). Sessions last 2 weeks.

3. **CSRF:** The frontend must fetch a CSRF token before POST/PUT/DELETE requests. The API client handles this.

4. **Mobile First:** Design for mobile screens first. Use Bulma's responsive classes.

5. **Type Safety:** Frontend uses TypeScript. Define types for API responses.

6. **PWA Support:** The frontend is configured as a Progressive Web App using `vite-plugin-pwa`:
   - Service worker auto-generated during build
   - Web app manifest at `/static/manifest.webmanifest`
   - iOS-specific meta tags for "Add to Home Screen" support
   - Screen Wake Lock API works better when installed as PWA on iOS
   - Icon: `frontend/public/icon.svg` (can be replaced with PNG icons for better compatibility)

## File Locations

| Purpose | Location |
|---------|----------|
| Django settings | `backend/config/settings.py` |
| API root | `backend/config/api.py` |
| URL routing | `backend/config/urls.py` |
| Auth endpoints | `backend/accounts/api.py` |
| Vue entry | `frontend/src/main.ts` |
| Vue router | `frontend/src/router/index.ts` |
| Auth store | `frontend/src/stores/auth.ts` |
| API client | `frontend/src/api/client.ts` |
| Global styles | `frontend/src/styles/main.scss` |
| Vite config (includes PWA) | `frontend/vite.config.ts` |
| PWA icon | `frontend/public/icon.svg` |

# Claude Code Instructions for Coach

This document provides instructions for AI agents working on this codebase.

## Working Directory Context

Commands should be run from specific directories:
- Backend commands: `cd backend` first, prefix with `DJANGO_SETTINGS_MODULE=config.settings`
- Frontend commands: `cd frontend` first

## Common Tasks

```bash
# Backend tests
cd backend && DJANGO_SETTINGS_MODULE=config.settings uv run pytest -v

# Frontend tests
cd frontend && npm run test:run

# Both dev servers at once, from the repo root (run `npm install` at the root once first)
npm run dev
```

**Note:** The production build uses `base: "/static/"` for Django static file serving. Use `npm run preview` (Vite's preview server) to test production builds locally - it handles the `/static/` base path correctly.

## Code Patterns

New API endpoints go in app-specific `backend/<app>/api.py` routers, registered in `backend/config/api.py`.

Frontend API calls go through `api` in `src/api/client.ts`.

Use the components in `src/components/ui/` (AppBar, Btn, Stepper, SetChips,
Sheet, MonthCalendar, Autocomplete, Icon) and the tokens in
`src/styles/tokens.scss`. Yellow (`--y`) means "live / act now" only: the app
bar, the current set, the primary action, the rest screen. Black (`--k`) means
state. Names and labels are condensed caps (`.caps`, `.eyebrow`); numbers and
comments stay regular width. Supersets are the only striped (`--hazard`) element.

## Important Notes

1. **DJANGO_SETTINGS_MODULE:** The environment has `DJANGO_SETTINGS_MODULE=settings.local` set. Always override with `DJANGO_SETTINGS_MODULE=config.settings` for Django commands.

2. **Session Auth:** The app uses Django session authentication (not JWT). Sessions last 2 weeks.

3. **CSRF:** The frontend must fetch a CSRF token before POST/PUT/DELETE requests. The API client handles this.

4. **Mobile First:** Design for a 390px-wide phone first; touch targets are at least 44px. The layout centers at `--content` width on larger screens.

5. **PWA:** Screen Wake Lock API works better when installed as PWA on iOS.

## File Locations

| Purpose | Location |
|---------|----------|
| Plan view (new plans, saved plans, editing finished sessions) | `frontend/src/views/PlanView.vue`, logic in `src/utils/plan.ts` |
| Live session state, saving, rest timer | `frontend/src/stores/activeSession.ts` |
| Rest screen (wake lock, alarm) | `frontend/src/components/RestTimer.vue`, `src/utils/audio.ts` |
| Exercise history cache | `frontend/src/composables/useExerciseHistory.ts` |
| What's New entries | `frontend/src/data/changelog.ts` |

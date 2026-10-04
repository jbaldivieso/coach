# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

(Installable PWA, used primarily on iPhone from the home screen. Mobile web, not native.)

## Users

The owner (who builds it) plus a small circle of friends who lift. Everyone knows each other; there is no anonymous public audience and no plan for one yet.

Primary situation: in the gym, phone in hand between sets, logging each set as it happens and running the rest timer. Hands may be sweaty or chalked, attention is split, and the phone gets picked up and put down constantly.

Secondary situations:
- Planning the next session shortly beforehand, on the phone. Today this is clumsy enough that the owner plans and records on a laptop with a timer on their watch; that is a failure of the product.
- Looking back: deciding whether to train today at all, checking when something was last done, following one exercise over time, or browsing what training looked like months ago.

## Product Purpose

Coach does three jobs:

- **Warehouse:** keep every lift so it can be found later: one exercise's history, when something was last done, what a past stretch of time looked like, a specific past day.
- **Plan:** put together the next session (exercises, order, sets, reps, weight) quickly on the phone, informed by what was done the last few times.
- **Track:** run the current session: where you are, rest timer, and what was actually lifted, with one tap per set.

Success means a session is planned on the phone in about a minute, logging never interrupts the lift, and no logged set is ever lost.

## Positioning

A personal, self-hosted tracker shaped around one person's actual training method rather than a generic template. It does not compete with Strong or Hevy on breadth; it wins by fitting the way its users train, staying minimal, and belonging to them.

- **Fits the method:** sets carry their own weight and reps (weight can change set to set), exercises and sessions take free-text comments, supersets share one rest, and the data model follows how the owner trains.
- **History at the point of decision:** while planning, each exercise shows its last three outings (sets and comments) drawn from real data, so progression is a judgment the lifter makes, not a rule the app imposes.
- **No bloat:** no social feed, no gamification, no upsells, no streaks, no prescriptive programming.
- **Owned:** the owner's own server and data, changed whenever they want.

## Operating Context

- Core loop: home (calendar + recent sessions) → start a session blank or from any past session → plan (each exercise shows its last three outings) → track (one exercise or superset at a time; marking a set done starts the rest timer; every set saves immediately) → history.
- Session titles are free text and only loosely predictable. Don't infer rotations, "next workout", or lineage from them. Exercise titles are the reliable key for history.
- The home calendar is used to decide whether to work out on a given day; it stays on home.
- Rest timer relies on Screen Wake Lock and audio cues; both are more reliable when installed as a PWA on iOS.
- Phone is repeatedly picked up mid-session; accidental gestures (e.g. iOS shake-to-undo) are a real hazard, and iOS may kill the PWA mid-session.
- The gym has connectivity; offline logging is not required.
- An in-app "What's New" changelog tells friends about new features.

## Capabilities and Constraints

- Stack: Django 6 + Django Ninja API, Vue 3 + TypeScript + Vite + Bulma, SQLite, deployed to the owner's own server (GCP). Session auth.
- Data model: Session (title, date, comments) → ordered Exercises (title, sets `[{weight, reps}]`, rest seconds, comments). Weight may be null (bodyweight).
- Plans set targets (number of sets, and reps/weight per set), but only actuals persist: a set's target is overwritten by what was lifted when it's marked done, and sets never done are dropped when the session finishes. No target-vs-actual record is kept.
- Supersets: adjacent exercises can be grouped to share one rest; grouped exercises always have the same number of sets.
- Exercise titles autocomplete from the user's own history.
- Exercises can be reordered and collapsed while editing.
- Session type (volume / weight / endurance / recovery) is being removed; it proved unhelpful.

## Brand Commitments

- Name: "Coach" (manifest uses "COACH").
- Voice: casual and wry among friends, e.g. the changelog's tongue-in-cheek "OUR NUMBER 1 MOST REQUESTED FEATURE!!!". Plain and quick in the UI itself.

## Evidence on Hand

- Real usage by the owner and friends; no testimonials, metrics, or public users. Don't fabricate any.

## Product Principles

1. **The lift comes first.** Anything used mid-set must work in a glance with one thumb and forgive clumsy input.
2. **Show the past, don't prescribe the future.** Put recent history beside every decision; never guess the next workout or auto-progress numbers.
3. **Never lose a set.** Saving continuously is part of logging, not polish.
4. **Fit the method, not the market.** Model how these users actually train; skip features that exist only because other trackers have them.
5. **Stay small.** Prefer removing friction over adding features; no engagement mechanics.
6. **Robust on the phone.** Installed-PWA behaviour (wake lock, sound, update prompts, gesture quirks) is part of the product, not polish.

## Accessibility & Inclusion

No specific requirement established beyond large, forgiving touch targets and legibility at arm's length under gym lighting, which follow from the primary usage scene.

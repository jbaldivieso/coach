---
name: Coach
description: A one-thumb weightlifting log and rest timer, styled as a safety signal.
colors:
  signal-yellow: "#ffd400"
  signal-black: "#161616"
  concrete: "#e9eae7"
  card: "#ffffff"
  chip: "#ecedea"
  muted: "#55585a"
  target: "#686b69"
  rule: "#d3d4d0"
  rule-strong: "#c9cac6"
  on-black: "#f4f4f2"
  on-black-muted: "#c9cac6"
  alert: "#e0261b"
  dim: "rgba(22, 22, 22, 0.32)"
typography:
  display:
    fontFamily: "Saira, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "min(140px, 36vw)"
    fontWeight: 800
    lineHeight: 0.9
    letterSpacing: "-0.02em"
    fontVariation: "'wdth' 75"
  dial:
    fontFamily: "Saira, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "48px"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "-0.03em"
    fontFeature: "'tnum'"
  headline:
    fontFamily: "Saira, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "28px"
    fontWeight: 800
    lineHeight: 1.1
    letterSpacing: "0.03em"
    fontVariation: "'wdth' 80"
  title:
    fontFamily: "Saira, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "18px"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "0.02em"
    fontVariation: "'wdth' 85"
  body:
    fontFamily: "Saira, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.45
    letterSpacing: "normal"
    fontFeature: "'tnum'"
  label:
    fontFamily: "Saira, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "12.5px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "0.06em"
    fontVariation: "'wdth' 85"
  section-label:
    fontFamily: "Saira, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "12px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "0.16em"
    fontVariation: "'wdth' 80"
rounded:
  sm: "4px"
  md: "6px"
  lg: "8px"
  sheet: "14px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  gutter: "16px"
  content: "608px"
components:
  button-primary:
    backgroundColor: "{colors.signal-yellow}"
    textColor: "{colors.signal-black}"
    rounded: "{rounded.md}"
    padding: "0 16px"
    height: "48px"
  button-primary-huge:
    backgroundColor: "{colors.signal-yellow}"
    textColor: "{colors.signal-black}"
    rounded: "{rounded.md}"
    padding: "0 16px"
    height: "64px"
  button-secondary:
    backgroundColor: "{colors.card}"
    textColor: "{colors.signal-black}"
    rounded: "{rounded.md}"
    padding: "0 16px"
    height: "48px"
  button-dark:
    backgroundColor: "{colors.signal-black}"
    textColor: "{colors.signal-yellow}"
    rounded: "{rounded.md}"
    padding: "0 16px"
    height: "48px"
  button-small:
    backgroundColor: "{colors.card}"
    textColor: "{colors.signal-black}"
    rounded: "{rounded.md}"
    padding: "0 12px"
    height: "44px"
  app-bar:
    backgroundColor: "{colors.signal-yellow}"
    textColor: "{colors.signal-black}"
    typography: "{typography.headline}"
    height: "56px"
  list-card:
    backgroundColor: "{colors.card}"
    textColor: "{colors.signal-black}"
    rounded: "{rounded.lg}"
    padding: "0 12px"
  text-field:
    backgroundColor: "{colors.card}"
    textColor: "{colors.signal-black}"
    rounded: "{rounded.md}"
    padding: "0 12px"
    height: "46px"
  set-chip:
    backgroundColor: "{colors.chip}"
    textColor: "{colors.signal-black}"
    padding: "6px 2px 5px"
  set-chip-selected:
    backgroundColor: "{colors.signal-yellow}"
    textColor: "{colors.signal-black}"
  progress-chip:
    backgroundColor: "{colors.card}"
    textColor: "{colors.muted}"
    rounded: "{rounded.sm}"
    padding: "0 12px"
    height: "44px"
  progress-chip-current:
    backgroundColor: "{colors.signal-black}"
    textColor: "{colors.signal-yellow}"
  stepper-number:
    backgroundColor: "{colors.card}"
    textColor: "{colors.signal-black}"
    typography: "{typography.dial}"
    rounded: "{rounded.md}"
    width: "140px"
  stepper-number-editing:
    backgroundColor: "{colors.signal-yellow}"
    textColor: "{colors.signal-black}"
  stepper-button:
    backgroundColor: "{colors.card}"
    textColor: "{colors.signal-black}"
    rounded: "{rounded.md}"
    size: "56px"
  calendar-day-trained:
    backgroundColor: "{colors.signal-black}"
    textColor: "{colors.signal-yellow}"
    rounded: "{rounded.sm}"
    height: "44px"
  resume-card:
    backgroundColor: "{colors.signal-black}"
    textColor: "{colors.signal-yellow}"
    rounded: "{rounded.lg}"
    padding: "12px 14px"
  sheet:
    backgroundColor: "{colors.card}"
    rounded: "{rounded.sheet}"
    padding: "8px 16px 16px"
  rest-screen:
    backgroundColor: "{colors.signal-yellow}"
    textColor: "{colors.signal-black}"
    typography: "{typography.display}"
  rest-screen-over:
    backgroundColor: "{colors.signal-black}"
    textColor: "{colors.signal-yellow}"
---

# Design System: Coach

## Overview

**Creative North Star: "Safety Signal"**

Coach is read at arm's length, mid-set, with one chalky thumb. The visual system borrows from industrial safety signage: a concrete-gray ground, white cards that hold content, black for anything that is state, and one high-visibility yellow that means "live, act now." Nothing decorates. Every color and every stripe carries a meaning the lifter can read in a glance.

The type is a single variable family, Saira, used two ways: names and labels squeezed into condensed uppercase, numbers and comments left at regular width so a weight or rep count reads instantly. Density is high but legible: rows are at least 44px tall, primary actions are 64px, and the big numbers on the Track and Rest screens are the largest things on any screen.

Depth is flat. Borders and fills do the work; shadows appear only under things that float over the page (menus, autocomplete). The one pattern element in the app is hazard tape, reserved for supersets.

**Key Characteristics:**
- Concrete ground, white cards, black state, yellow signal.
- One variable family (Saira), condensed caps for names, regular-width tabular numerals for data.
- Sticky yellow app bar on top, sticky concrete dock with the screen's main action on the bottom.
- Flat surfaces with crisp black borders on anything active or tappable-primary.
- Hazard tape marks supersets and nothing else.
- Fast, short motion; reduced motion respected.

## Colors

A signal palette: one loud yellow, one near-black, and quiet grays for everything else.

### Primary
- **Signal Yellow** (`--y`): Live / act now. The app bar, the primary action in the dock, the current set (ledger row, selected set chip), a number being typed in a stepper, the current-exercise tag, the Rest pill, the whole Rest screen, and the newest point on an exercise chart. Also used as text on black.

### Secondary
- **Signal Black** (`--k`): State. Trained days on the calendar, the current exercise in the Track progress strip, the Resume card, superset headers, toggled-on controls (BW, open menu button), dark buttons, chart dots and tooltips. Also all primary text, 2px borders on primary and current elements, and the focus ring.

### Tertiary
- **Alert Red** (`--alert`): Errors and destruction only. Error borders on fields and invalid exercise cards, field error text, the "Delete this plan/session" link and danger menu actions, and the unread dot on the menu button.

### Neutral
- **Concrete** (`--concrete`): Page ground, dock background, and the html background behind safe areas.
- **Card White** (`--card`): Cards, lists, sheets, fields, secondary buttons, stepper controls.
- **Chip Gray** (`--chip`): Read-only set chips and the pressed state of stepper +/- and autocomplete rows.
- **Muted Ink** (`--muted`): Secondary text, sub-lines, units, section labels, placeholder chevrons.
- **Target Gray** (`--target`): Planned-but-not-done values in the Track ledger. Chosen for 4.5:1 on concrete; lighter values failed contrast.
- **Rule** (`--rule`): 1px row dividers, dock top border, chart gridlines.
- **Rule Strong** (`--rule-strong`): 1.5px borders on fields, stepper buttons, inactive progress chips and round cards; the sheet grab handle.
- **On Black** (`--on-k`) and **On Black Muted** (`--on-k-muted`): Body and secondary text placed on black surfaces.
- **Dim** (`--dim`): Scrim behind sheets and the open menu.

### Named Rules
**The Signal Rule.** Yellow means live or act now. It never decorates, never fills a section just to add color, and never marks something that is merely selected in the past. If nothing on the screen needs the lifter right now, the only yellow is the app bar.

**The State Rule.** Black means "this is state": done, current, linked, toggled on. A new indicator of state is black (with yellow or on-black text), not a new color.

**The Ground Rule.** Concrete is the ground; white cards hold content. Don't put cards on white or content directly on concrete without a card unless it is a heading, a section label, or the Track ledger.

**The Red Line Rule.** Red is for errors, destructive actions, and the unread dot. It is never a highlight, a brand accent, or a warning about something that is not wrong.

## Typography

**Display Font:** Saira (variable, wdth 75–100, wght 400–800; loaded from Google Fonts), with system-ui fallback
**Body Font:** Saira, same family
**Label Font:** Saira, condensed via `font-stretch`

**Character:** One utilitarian sans in two widths. Condensed caps read like stenciled labels; regular-width tabular numerals read like a gauge.

### Hierarchy
- **Display** (800, min(140px, 36vw), 0.9, width 75%): The rest clock only.
- **Dial** (800, 48px, 1, regular width, -0.03em): The big weight and reps numbers in Track steppers. The Plan editor's stepper uses the same treatment at 30px.
- **Headline** (800, 28px, 1.1, width 80%, uppercase): App bar titles (19px in the compact bar). The current exercise name on Track runs larger (36px, 24px when long) at the same width.
- **Title** (800, 18px, width 85%, uppercase): Exercise names on cards; sheet titles run at 22px / width 80%. Month heading on Home is 16px.
- **Body** (400, 15px, 1.45, tabular): Everything else, including row titles (700) and comments (italic, muted). Inputs are 16px so iOS doesn't zoom. Secondary lines are 13px; fine print 12.5px.
- **Label** (700–800, 11–13.5px, width 85%, uppercase, 0.04–0.06em): Small buttons, inline actions (Add a round, Copy down), ledger row names, track sub-line, unit labels (0.1–0.16em).
- **Section Label** (700, 12px, width 80%, uppercase, 0.16em, muted): The heading that names a list section ("Recent", "Sessions", "Session comments", changelog dates). It is the section's heading, not a tag above another heading.

### Named Rules
**The Two Widths Rule.** Names and labels are condensed caps; numbers, comments, and free text stay regular width and mixed case. Never set a number in condensed caps, and never set a user's comment in caps.

**The Tabular Rule.** Body text is tabular (`font-variant-numeric: tabular-nums`) everywhere so columns of weights and reps line up.

## Layout

Phone-first, single column, centered at the content width (608px) on anything wider. There are no breakpoints; the gutter grows by `max(16px, (100% - 608px) / 2)`.

Every screen is a **screen** (full-height flex column) containing the app bar, a **screen body** (12px top, 28px bottom, gutter sides), and optionally a **dock**: sticky to the bottom, concrete with a 1px rule on top, 10px padding plus `14px + env(safe-area-inset-bottom)` below, holding one full-width action or a two-up pair with 8px gaps. The app bar adds `env(safe-area-inset-top)`. Sheets and the rest screen use `16px + safe-area` and `18px + safe-area` at the bottom.

Rhythm runs on 4px steps: 4px between set chips, 6–8px between cards and controls, 10–12px card padding, 16px gutter, 20px above section labels. Rows are a minimum 52px tall with 11px vertical padding and a 1px rule between them; the last row has none.

The Track ledger and the current ledger row break out of the gutter (full-bleed yellow band) to make "now" unmistakable.

### Named Rules
**The Thumb Rule.** The action the lifter needs next lives in the dock at the bottom, within thumb reach. New screens with a main action put it in the dock, not the app bar or mid-page.

## Elevation & Depth

Flat by default. Depth comes from fill contrast (white on concrete, black on white) and border weight (1.5px quiet, 2px black for primary/current). Shadows appear only on layers that float over content: the overflow menu, the autocomplete list, and the PWA update prompt. Inset 2px rings (black for selected set chips, red for invalid exercise cards) mark state without lifting anything.

### Shadow Vocabulary
- **Float** (`box-shadow: 0 10px 24px rgba(0, 0, 0, 0.25)`): Popovers and menus that sit above the page. Always paired with a 2px black border.

### Named Rules
**The Flat Page Rule.** Nothing that sits in the page flow casts a shadow. If an element needs emphasis, give it a black border or a state fill.

## Shapes

Small, firm corners: 4px for chips, calendar days, and tooltips; 6px for buttons, fields, stepper parts, and the app bar icons; 8px for cards, lists, menus, and notices; 14px top corners on bottom sheets. The superset group uses a slightly rounder 10px container. Borders come in three weights: 1px rules, 1.5px quiet outlines (rule-strong), 2px black for primary, current, and floating elements.

Icons are 24-unit stroke icons drawn inline (2px stroke, round caps and joins, `currentColor`), shown at 20px or 16px. They inherit text color, so yellow-on-black and black-on-yellow come for free.

### Named Rules
**The Hazard Tape Rule.** The only striped element in the app is hazard tape (`--hazard`: 45° yellow and black, 6px bands), and it marks supersets: a thin strip across the top of the black superset header in Plan and Session detail. Never use stripes for anything else, and never mark a superset without it.

## Components

### Buttons
Tactile and blunt: square-ish, bordered, scale down slightly when pressed.
- **Shape:** 6px corners, 1.5px black border (2px on primary and dark), minimum 48px tall, 700 weight at 15px.
- **Primary:** Signal yellow fill. The screen's one main action, usually in the dock.
- **Secondary (default):** White fill, black border.
- **Dark:** Black fill, yellow text. Strong action that isn't "the" action (Skip on Rest).
- **Ghost:** No border or fill.
- **Sizes:** Huge (64px, 19px condensed caps 800) for the dock's main action on Track and Finish; Small (44px, 13.5px condensed caps) for app bar actions like Finish.
- **States:** Pressed scales to 0.98 (80ms); disabled at 45% opacity; loading at 70% with `aria-busy`. Focus uses the global ring.

### Set Chips
The signature data element: a fixed 6-column grid of weight-over-reps tiles.
- **Grid:** Always six equal columns with 4px gaps, regardless of how many sets exist, so set N lines up across every row on a screen. No exercise exceeds six sets.
- **Style:** Chip gray (or white when on a gray context), 5px corners. Weight on top (800), `×reps` below (600, muted ×).
- **Selectable:** When tappable they are at least 44px tall and `aria-pressed`. Selected is yellow with an inset 2px black ring.
- **Done (Edit mid-session):** Black with on-black text and disabled: logged sets are fixed on Lift, not in the editor. A muted "✓ N done · fix those on Lift" line sits under them, and the set count can't drop below them.

### Cards / Lists
- **Corner Style:** 8px.
- **Background:** White on concrete.
- **Shadow Strategy:** None (see Elevation).
- **Border:** None for lists and collapsed exercises; 1.5px rule-strong for round cards; 2px black for the current round card, the set editor, and the superset group.
- **Internal Padding:** 10–12px; lists pad 12px sides with rows inside.
- **Rows:** Optional date column (46px: bold 17px day over 13px muted weekday), a bold title, and a muted single-line ellipsized sub-line.
- **Resume card:** Black, yellow title, on-black sub-line, 60px minimum. The way back into an open session.
- **Plan exercise (open):** Its header (name, rest, ⋯, and a 44px fold button with a 1.5px black outline) sticks under the app bar while you scroll inside the exercise, gaining a 1px rule once stuck. In a superset the black header sticks instead, with a yellow fold icon.
- **Plan exercise (collapsed):** Name, muted clock + rest (hidden inside a superset, whose header shows it), a chevron, and the planned set chips. Folding leaves every exercise collapsed; the one just folded wears a 2px black ring (a superset, a 2px black outline) for about a second.

### Inputs / Fields
- **Style:** White, 1.5px rule-strong border, 6px corners, minimum 46px, 16px input text. Textareas start at 76px.
- **Focus:** Border turns black with a 1px black outer ring.
- **Error:** Red border, red 13px/600 message below. Dashed borders mark optional note fields in Plan.
- **Session note:** Under the date on every Plan screen (first after the title in Edit): a dashed note field with a pencil and a one-line textarea that grows as you type. With text it turns solid and gains a small "Session note" caps label. On Track the same note is a "Note on today" row under the exercise note, opening the note sheet.
- **Autocomplete:** Floating white list, 2px black border, Float shadow, 46px rows; the active row is chip gray.

### Stepper
The way numbers are entered mid-set.
- **Large (Track):** 56px − and + buttons (white, 1.5px rule-strong, 6px) flanking a 140px number box (white, 2px black border, Dial type) with the unit in small spaced caps beneath.
- **Medium (Plan editor):** 48px buttons, 104px box, 30px number, unit to the right.
- **Editing:** Tapping the number turns it into a yellow input; Enter moves to the next stepper (weight to reps). Bodyweight displays as "BW".

### Navigation
- **App bar:** Sticky, yellow, 56px (`--appbar-h` includes the top safe area). The COACH wordmark (800, 21px, width 75%, 0.05em) sits on the left of every screen and goes home; on Home it is the 28px title itself. Elsewhere a 1.5px black vertical rule follows it, then a back arrow only when back leads somewhere other than home (a route like Past year, history such as search results, or the rest screen's hide), then the 19px condensed-caps title, optional actions, and the ⋯ menu always last in the same spot. Icon buttons are 44px. The open menu button turns black with a yellow icon. Screens with unsaved edits guard every way out (COACH, back, the menu) with one prompt.
- **Lift / Edit switch:** On a live session the bar drops its title for a segmented control after the rule: two 41px halves in a 1.5px black outline, condensed caps; the current mode is black with yellow text. It replaces the route, so switching never stacks history. Edit is the Plan editor on the live session; leaving it for Lift or Finish saves.
- **Menu:** White popover, 2px black border, Float shadow, over the dim scrim. Holds What's new and Log out. A red unread dot (8px, ringed in the bar's color) marks new changelog entries.
- **Track progress strip:** Horizontally scrolling 44px chips (white, 1.5px border, 4px corners); done chips go black text, the current one is black with yellow text; a black + button adds an exercise. The strip fades out under the + button.

### Bottom Sheet
White, 14px top corners, max 72px below the top, grab handle, condensed-caps title. Slides up 40px with a fade (200–220ms, `cubic-bezier(0.2, 0.8, 0.2, 1)`) over the dim scrim.

### Calendar
Seven columns, 44px day cells with 4px corners on a white card. Trained days are black with yellow numerals; today has a 2px black outline; days outside the month are muted at 45%. The year view uses tiny square cells, black for trained.

### Exercise Chart
White card, rule gridlines, black dots ringed in white; the newest point is yellow with a black ring. Tooltip is a black chip with on-black text. Points are focusable.

### Rest Screen
A full-screen takeover that is the clearest signal in the app.
- **Running:** Whole screen yellow, transparent app bar, Display clock, "of 2:00" line, a 14px black progress bar (scaleX, linear), a "Next" line under a 2px rule, a note link, and four 60px buttons (−15, +30, Pause/Go, Skip as dark).
- **Paused:** Same layout; the "of" line reads "Paused" and the button reads "Go".
- **Over:** Flips to black with yellow text; "Up" replaces "Next" at 24px; two buttons, +30 and a yellow primary to go to the set. It ends on black.
- **Rest pill:** On Track, a 44px yellow pill with a black border shows a running rest and returns to it.

### Notices
White card with a 2px black border (red when it's an error), condensed-caps bold lead line, and an underlined action link.

## Do's and Don'ts

### Do:
- **Do** give every tappable thing at least a 44px target; dock actions are 48px, main actions 64px.
- **Do** keep text at 4.5:1 or better. Use Target Gray for planned values on concrete, never anything lighter.
- **Do** rely on the global focus ring (3px solid black, 2px offset) and never remove it.
- **Do** put the screen's main action in the dock, yellow, and make it the only yellow button on screen.
- **Do** use black with yellow (or on-black) text for anything that shows state: done, current, linked, toggled.
- **Do** keep numbers regular width and tabular; condense and capitalize names and labels.
- **Do** keep motion short (80–250ms), on transform and opacity, and make sure it collapses under `prefers-reduced-motion`.
- **Do** pad the dock, sheets, and app bar with the safe-area insets.
- **Do** use the six-column set chip grid for any row of sets, even when an exercise has fewer than six.

### Don't:
- **Don't** use yellow to decorate, to brand a section, or to fill an empty state.
- **Don't** use stripes or hazard tape for anything but supersets.
- **Don't** use red for warnings, highlights, or emphasis; it is errors, destructive actions, and the unread dot.
- **Don't** add shadows to cards, rows, or buttons in the page flow.
- **Don't** set comments, numbers, or free text in condensed caps.
- **Don't** put a small tag or label above a heading; a section label is the section's only heading.
- **Don't** introduce a second typeface or an icon font; icons are inline stroke SVGs in `currentColor`.
- **Don't** hard-code grays; use the neutral tokens.

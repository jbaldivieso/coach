# Training Plan Generator Prompt

## Quick Context
- **Database**: `training.db` (in project root)
- **Athlete Profile**: 49M, 25-35 miles/week running, injury-prone (feet/Achilles/plantar fasciitis), left foot pronation issues
- **Primary Goal**: Stay injury-free above all else
- **Next Event**: Deception Pass 25K (Dec 14, 2025) - 3000' elevation gain, technical trails
- **Weekly Schedule**: 
  - Futsal every Monday night (high intensity, hardwood pounding)
  - High-intensity runs: Wednesday (up to 7mi, tempo/hills), Saturday (distance)
  - Recovery runs: other days (Tuesday runs happen midday after futsal recovery)
  - Lifting: weekday evenings, Sunday midday
  - Abs: 6-8min planks 2-3x/week (separate, no need to plan)

*See TRAINING_GOALS.md for full background, schema.sql for database structure*

---

## Your Task

1. **Query recent training history**:
   - Past 3 months of running (from `activities` table)
   - Past 2 months of strength training (from `lifting_sessions` and `lifting_exercises` tables)

2. **Create or update weekly plans for the next 3 weeks** (weeks start Monday):
   - **Week 1 (current)**: Detailed, specific workouts
   - **Weeks 2-3**: High-level sketch, key sessions outlined
   - If plans already exist, update **only if needed**
   - For current week updates, add brief note to `weekly_plans.description` explaining changes (or confirming we're staying the course)

3. **Insert/update data** into:
   - `weekly_plans` (week-level guidance)
   - `planned_runs` (date, distance, type, description, priority)
   - `planned_lifting_sessions` (date, name, description, priority)
   - `planned_lifting_exercises` (exercise_name, reps_per_set as JSON array, rest_seconds, notes)

---

## Planning Principles

### Running
- Analyze overall periodization leading to Deception Pass 25K
- Check Strava notes (`activities.notes`, `activities.description`) for fatigue cues
- Progressive loading - avoid spikes
- Account for futsal impact on Monday nights
- Build vertical/technical capacity for 3000' gain event
- Prioritize injury prevention over performance gains

### Strength Training
- **Exercises**: Prefer pull-ups, bench, RDL, deadlift; ok to rotate monthly
- **Prescription**: Exercise name, sets × reps (e.g., `[10, 10, 8]`), rest intervals
- **Weight**: NOT prescriptive - use historical data as reference but let athlete auto-regulate
- **Recovery timing**: Ensure proper spacing between running and lifting (follow current science for 49-year-old athlete)
- **Load management**: Adjust volume based on running load and cumulative fatigue

### Weekly Plan Notes
In `weekly_plans.description`, include:
- **Rationale**: Why this week's structure makes sense
- **Recovery guidance**: Sleep, nutrition, stretching priorities
- **Warning signs**: What to watch for (fatigue, injury indicators)
- **Adaptations**: When to back off or skip sessions
- (All description fields can use markdown.)

---

## Quality Control

Before finalizing, verify:
- [ ] Rate of increase is conservative and appropriate for injury history
- [ ] Timeline aligns with Deception Pass 25K on Dec 14, 2025
- [ ] Adequate recovery between high-intensity sessions
- [ ] Lifting doesn't compromise running recovery
- [ ] Plan accounts for weekly futsal impact
- [ ] Vertical/elevation training is progressive and sufficient

---

## Output Format

After generating the plan:
1. Show SQL INSERT/UPDATE statements (for transparency)
2. Provide human-readable summary of the 3-week plan
3. Highlight any key decisions or trade-offs made
4. Note any concerns or things to monitor

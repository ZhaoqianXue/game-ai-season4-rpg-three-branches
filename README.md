# Season 4: RPG — The Living Village

Ten residents follow a visible day: leave home for distinct jobs, take a short staggered break at the inn, finish their work, then return home to sleep. A nearby visitor gets a brief greeting without stopping village life for the rest of the day.

## Design and reflection

This agent builds on the course's [Neighbor example](https://github.com/vox-deorum/game-agent-template/tree/examples/three_branches/neighbor). Each resident chooses a routine and destination from its own observation and memory. Night takes priority over social reactions. During the day, a greeting lasts at most 18 ticks and cannot restart within 120 ticks. Afterward, the resident resumes the schedule for the current phase.

Midday breaks start three ticks apart and last 90 ticks per resident. Two stall keepers also meet briefly by the well in the evening before going home; the others continue working. Phase announcements and scripted visitor replies explain these changes. Replies to one visitor are limited to one per 80 ticks, and neighbor conversations retain the starter's turn limit.

Season 3 feedback praised recognizable neighbors but reported repeated greetings, long meetings, stuck characters, and jerky movement. The bounded encounters and reply cooldown address repetition. Walking slows near the next waypoint to reduce overshoot, and stalled routes penalize occupied cells. Connected-region checks prevent a prop's nearest walkable cell from becoming an unreachable destination. A full-day seed-23 probe exposed that last failure: the board worker originally never worked even though the episode could still score 100.

A schedule with priority-based interruptions was chosen over unrestricted wandering or model-generated plans because its transitions are easy to test. The tradeoff is predictable behavior and limited dialogue. Crowding can still delay arrival, and a meeting's fixed time budget includes travel, so distant residents may spend less time together. Completion scores alone do not measure these social qualities.

## Rating question

On a scale of 1–5, how clearly did the villagers follow a daily routine while briefly acknowledging the visitor and then returning to their activities?

## Local verification

Use Python 3.12 and the pinned dependencies. `season.json` contains the downloaded Season 4 settings: `seat_plan=cast_10` and `daynight=true`.

```console
python -m sandbox test
python -m sandbox eval
python verify_day.py --seeds 0 11 23
python -m sandbox play --seed 23
```

The full-day probe checks legal actions, actual successful work, all ten residents reaching home and sleeping, and decision latency. It uses the supplied scripted visitor with a seeded random stream for repeatability. Browser visitor play is checked separately.

The final test suite passed 110 tests with seven supplied Gymnasium input-casting warnings. Official-harness evaluation with Season 4 settings scored 100.00 on each seed from 0 through 4 (mean 100.00). In the seed-23 behavior regression, all ten residents worked and ended the 1,200-tick day asleep at home; the slowest decision took 42.10 ms locally, below the 250 ms limit.

The same behavioral checks passed on seeds 0 and 11, with all ten residents working and sleeping at home. Their maximum local decision times were 9.99 and 18.22 ms respectively. These measurements are local checks, not guarantees about server timing or human ratings.

Codex also controlled the visitor through a complete seed-23 browser day, ending at tick 1,200 with the cast scoring 100. The visit verified a bell worker's reply, the midday gathering and departures, the two stall keepers' evening well meeting, and the darker night with residents asleep at home. The browser view covered visited areas; the full-cast assertions came from the separate probes.

## AI-use disclosure and reflection

OpenAI Codex substantially assisted with the schedule, scripted dialogue, cooldowns, navigation changes, tests, verification scripts, and this README. The supplied Neighbor implementation remains the base. Codex ran the local checks and handled the delegated browser workflow; these are not claims that the student personally performed those actions.

The main lesson from verification was that a legal action and a perfect completion score can hide a resident doing no useful work. Behavioral assertions caught the unreachable board approach and guided the fix. AI-generated changes needed those checks rather than acceptance based on a passing score. No LLM requests are used by the submitted dialogue policy. The framework, manifest, and pinned dependency files are unchanged.

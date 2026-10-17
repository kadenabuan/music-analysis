# builds dashboard/data.json (summaries only, no raw rows) for dashboard/index.html
import json
from datetime import datetime, timedelta
from pathlib import Path

MIN_PLAY_MS = 30_000  # Spotify counts a stream after 30 seconds

here = Path(__file__).resolve().parent
files = sorted(here.glob("Streaming_History_Audio_*.json"))

data = []
for file in files:
    with file.open("r", encoding="utf-8") as f:
        data.extend(json.load(f))

# timestamps are UTC; convert to local time so plays land on the right day
times = [
    datetime.fromisoformat(entry["ts"].replace("Z", "+00:00")).astimezone()
    for entry in data
]

first_date = min(times).date()
last_date = max(times).date()

daily_totals = {}
current_date = first_date
while current_date <= last_date:
    daily_totals[current_date.isoformat()] = 0
    current_date += timedelta(days=1)

track_totals = {}
habit_totals = {}
for entry, played_at in zip(data, times):
    ms = entry["ms_played"]
    month = played_at.strftime("%Y-%m")
    daily_totals[played_at.date().isoformat()] += ms

    habit_key = (month, played_at.weekday(), played_at.hour)
    habit_totals[habit_key] = habit_totals.get(habit_key, 0) + ms

    track_name = entry.get("master_metadata_track_name")
    artist = entry.get("master_metadata_album_artist_name")
    if track_name and artist:
        track_key = (artist, track_name, month)
        plays, listening_ms = track_totals.get(track_key, (0, 0))
        counted = 1 if ms >= MIN_PLAY_MS else 0
        track_totals[track_key] = (plays + counted, listening_ms + ms)

output = {
    "meta": {
        "first_date": first_date.isoformat(),
        "last_date": last_date.isoformat(),
        "total_ms": sum(entry["ms_played"] for entry in data),
        "min_play_ms": MIN_PLAY_MS,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    },
    "daily": daily_totals,
    "tracks": [[*key, plays, ms] for key, (plays, ms) in track_totals.items()],
    "habits": [[*key, ms] for key, ms in habit_totals.items()],
}

out_path = here / "dashboard" / "data.json"
out_path.parent.mkdir(exist_ok=True)
out_path.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"wrote {out_path} ({out_path.stat().st_size / 1_000_000:.2f} MB)")
print(f"{len(output['tracks']):,} track-month rows, {len(output['habits']):,} habit rows")

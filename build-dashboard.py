# builds dashboard/data.json (summaries only, no raw rows) for dashboard/index.html
import csv
import json
from datetime import date, datetime, timedelta
from pathlib import Path

MIN_PLAY_MS = 30_000  # Spotify counts a stream after 30 seconds

# mood map: intensity (how fast/loud/energetic) against valence (how positive)
INTENSITY_WEIGHTS = {"energy": 0.5, "tempo": 0.25, "loudness": 0.25}
TEMPO_RANGE = (60, 180)  # BPM mapped onto 0..1
LOUDNESS_RANGE = (-30, 0)  # dB mapped onto 0..1
INTENSITY_CUTOFF = 0.5
VALENCE_CUTOFF = 0.5
NEW_RELEASE_DAYS = 365  # a play counts as a new release within a year of the song's release

here = Path(__file__).resolve().parent
files = sorted(here.glob("Streaming_History_Audio_*.json"))

data = []
for file in files:
    with file.open("r", encoding="utf-8") as f:
        data.extend(json.load(f))


def scale(value, low, high):
    return min(1.0, max(0.0, (value - low) / (high - low)))


def mood_of(intensity, valence):
    if intensity >= INTENSITY_CUTOFF:
        return "Hyped" if valence >= VALENCE_CUTOFF else "Intense"
    return "Chill" if valence >= VALENCE_CUTOFF else "Moody"


def parse_release(value):
    parts = value.split("-")
    # some exports have blank or placeholder dates like 0000
    if not parts[0].isdigit() or int(parts[0]) < 1900:
        return None
    year = int(parts[0])
    month = int(parts[1]) if len(parts) > 1 else 1
    day = int(parts[2]) if len(parts) > 2 else 1
    return date(year, month, day)


# playlist exports give each song its genres, release date and audio features;
# only those per-song details are used, never playlist names or who added a song
track_info = {}
for file in sorted((here / "spotify_playlists").glob("*.csv")):
    with file.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            uri = row["Track URI"]
            if uri in track_info or not row["Energy"]:
                continue
            energy = float(row["Energy"])
            valence = float(row["Valence"])
            intensity = (
                INTENSITY_WEIGHTS["energy"] * energy
                + INTENSITY_WEIGHTS["tempo"] * scale(float(row["Tempo"]), *TEMPO_RANGE)
                + INTENSITY_WEIGHTS["loudness"] * scale(float(row["Loudness"]), *LOUDNESS_RANGE)
            )
            track_info[uri] = {
                "genres": [g.strip() for g in row["Genres"].split(",") if g.strip()],
                "released": parse_release(row["Release Date"]),
                "energy": energy,
                "valence": valence,
                "dance": float(row["Danceability"]),
                "tempo": float(row["Tempo"]),
                "acoustic": float(row["Acousticness"]),
                "intensity": intensity,
                "mood": mood_of(intensity, valence),
            }

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
mood_totals = {}
mood_hour_totals = {}
sound_totals = {}
genre_totals = {}
era_totals = {}
new_release_totals = {}
coverage_ms = 0
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

    info = track_info.get(entry.get("spotify_track_uri"))
    if not info or ms == 0:
        continue
    coverage_ms += ms
    mood_key = (month, info["mood"])
    mood_totals[mood_key] = mood_totals.get(mood_key, 0) + ms
    mood_hour_key = (month, played_at.hour, info["mood"])
    mood_hour_totals[mood_hour_key] = mood_hour_totals.get(mood_hour_key, 0) + ms

    # sums weighted by listening time, so the page can average over any range
    sums = sound_totals.setdefault(month, [0, 0, 0, 0, 0, 0, 0])
    for i, value in enumerate((1, info["energy"], info["valence"], info["dance"],
                               info["tempo"], info["intensity"], info["acoustic"])):
        sums[i] += value * ms

    # a song with several genres splits its time evenly between them
    for genre in info["genres"]:
        genre_key = (month, genre)
        genre_totals[genre_key] = genre_totals.get(genre_key, 0) + ms / len(info["genres"])

    if info["released"]:
        era_key = (month, info["released"].year)
        era_totals[era_key] = era_totals.get(era_key, 0) + ms
        if 0 <= (played_at.date() - info["released"]).days <= NEW_RELEASE_DAYS:
            new_release_totals[month] = new_release_totals.get(month, 0) + ms

output = {
    "meta": {
        "first_date": first_date.isoformat(),
        "last_date": last_date.isoformat(),
        "total_ms": sum(entry["ms_played"] for entry in data),
        "coverage_ms": coverage_ms,
        "min_play_ms": MIN_PLAY_MS,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    },
    "daily": daily_totals,
    "tracks": [[*key, plays, ms] for key, (plays, ms) in track_totals.items()],
    "habits": [[*key, ms] for key, ms in habit_totals.items()],
    "moods": [[*key, ms] for key, ms in mood_totals.items()],
    "mood_hours": [[*key, ms] for key, ms in mood_hour_totals.items()],
    # [month, covered_ms, energy·ms, valence·ms, dance·ms, tempo·ms, intensity·ms, acoustic·ms]
    "sound": [[month, *(round(v) for v in sums)] for month, sums in sound_totals.items()],
    "genres": [[*key, round(ms)] for key, ms in genre_totals.items()],
    "eras": [[*key, ms] for key, ms in era_totals.items()],
    "new_releases": [[month, ms] for month, ms in new_release_totals.items()],
}

out_path = here / "dashboard" / "data.json"
out_path.parent.mkdir(exist_ok=True)
out_path.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"wrote {out_path} ({out_path.stat().st_size / 1_000_000:.2f} MB)")
print(f"{len(output['tracks']):,} track-month rows, {len(output['habits']):,} habit rows")
print(f"{len(track_info):,} songs with playlist details; "
      f"they cover {coverage_ms / output['meta']['total_ms']:.0%} of listening time")

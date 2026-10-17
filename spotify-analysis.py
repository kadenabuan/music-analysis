# main setup
import json
from datetime import datetime, timedelta
from pathlib import Path

MIN_PLAY_MS = 30_000  # Spotify counts a stream after 30 seconds

files = sorted(Path(__file__).resolve().parent.glob("Streaming_History_Audio_*.json"))

data = []

for file in files:
    with file.open("r", encoding="utf-8") as f:
        data.extend(json.load(f))

print(len(data))
if data:
    print("Headers:", list(data[0].keys()))


def format_duration(duration_ms):
    hours, minutes = divmod(round(duration_ms / 60_000), 60)
    minute_label = "minute" if minutes == 1 else "minutes"
    if hours == 0:
        return f"{minutes} {minute_label}"
    hour_label = "hour" if hours == 1 else "hours"
    return f"{hours:,} {hour_label} and {minutes} {minute_label}"


total_ms = sum(entry["ms_played"] for entry in data)
print(f"total playing time: {format_duration(total_ms)}")


if data:
    # timestamps are UTC; convert to local time so plays land on the right day
    dates = [
        datetime.fromisoformat(entry["ts"].replace("Z", "+00:00")).astimezone().date()
        for entry in data
    ]
    first_date = min(dates)
    last_date = max(dates)

    daily_totals = {}
    current_date = first_date
    while current_date <= last_date:
        daily_totals[current_date] = 0
        current_date += timedelta(days=1)

    for entry, listening_date in zip(data, dates):
        daily_totals[listening_date] += entry["ms_played"]

    monthly_totals = {}
    monthly_day_counts = {}
    yearly_totals = {}
    yearly_day_counts = {}
    for listening_date, listening_ms in daily_totals.items():
        month = listening_date.strftime("%Y-%m")
        year = listening_date.year
        monthly_totals[month] = monthly_totals.get(month, 0) + listening_ms
        monthly_day_counts[month] = monthly_day_counts.get(month, 0) + 1
        yearly_totals[year] = yearly_totals.get(year, 0) + listening_ms
        yearly_day_counts[year] = yearly_day_counts.get(year, 0) + 1

    print("\nAverage listening time per calendar day:")
    print(f"Overall: {format_duration(total_ms / len(daily_totals))}")
    print("By month:")
    for month in sorted(monthly_totals):
        average_ms = monthly_totals[month] / monthly_day_counts[month]
        print(f"{month}: {format_duration(average_ms)}")
    print("By year:")
    for year in sorted(yearly_totals):
        average_ms = yearly_totals[year] / yearly_day_counts[year]
        print(f"{year}: {format_duration(average_ms)}")

artist_totals = {}
for entry in data:
    artist = entry.get("master_metadata_album_artist_name")
    if artist:
        listening_ms, track_plays = artist_totals.get(artist, (0, 0))
        counted = 1 if entry["ms_played"] >= MIN_PLAY_MS else 0
        artist_totals[artist] = (listening_ms + entry["ms_played"], track_plays + counted)

print("\nTop 20 artists by listening time:")
top_artists = sorted(artist_totals.items(), key=lambda item: item[1][0], reverse=True)[:20]
for rank, (artist, (listening_ms, track_plays)) in enumerate(top_artists, start=1):
    print(f"{rank}. {artist}: {format_duration(listening_ms)} ({track_plays:,} track plays)")

track_totals = {}
for entry in data:
    track_name = entry.get("master_metadata_track_name")
    artist = entry.get("master_metadata_album_artist_name")
    if track_name and artist and entry["ms_played"] >= MIN_PLAY_MS:
        track_key = (artist, track_name)
        track_totals[track_key] = track_totals.get(track_key, 0) + 1

print("\nTop 20 most played songs of all time:")
top_tracks = sorted(track_totals.items(), key=lambda item: item[1], reverse=True)[:20]
for rank, ((artist, track_name), plays) in enumerate(top_tracks, start=1):
    print(f"{rank}. {track_name} - {artist}: {plays:,} plays")


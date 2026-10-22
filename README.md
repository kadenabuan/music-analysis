# Listening Years

An interactive dashboard of three years of my Spotify listening history, from August 2023 to September 2026.

**Live site:** https://kadenabuan.github.io/music-analysis/

## What it shows

- **Listening over time:** average minutes per day, by month or by year, optionally split by mood
- **Mood map and mood by time of day:** whether I was listening to chill, hyped, moody or intense music
- **How the music sounded:** monthly energy, positivity, danceability and tempo
- **Top artists and songs:** ranked by listening time or by number of plays
- **Genres and song era:** top genres, genres over time, and when the songs came out
- **When I listen:** a weekday-by-hour heatmap of average listening
- **Artist lookup:** any artist's monthly listening and their top songs

A date-range filter at the top applies to every view.

## How it works

1. Spotify's [Extended Streaming History](https://www.spotify.com/account/privacy/) export provides one JSON row per play.
2. `build-dashboard.py` reads the audio files and converts UTC timestamps to local time. It then sums everything into totals by song and month, by day, and by weekday and hour, and writes `dashboard/data.json`.
3. Playlist exports in `spotify_playlists/` (CSV files from a tool like [Exportify](https://exportify.app/)) give each song its genres, release date and audio features. They're matched to plays by track ID, so mood, sound, genre and era views cover songs that appear in at least one playlist (about two thirds of my listening time). Playlist names and who added each song are never published.
4. `dashboard/index.html` loads that file and draws the charts in the browser with [Chart.js](https://www.chartjs.org/).

Each song's mood comes from two scores: intensity (energy, tempo and loudness combined) and positivity (Spotify's valence). Fast, loud songs are Hyped or Intense, and slower, softer ones Chill or Moody, depending on positivity. The weights and cutoffs are constants at the top of `build-dashboard.py`.

A play counts once it reaches 30 seconds, the same rule Spotify uses for a stream. Listening time includes every second played.

`spotify-analysis.py` is the original command-line version, which prints the same summaries as text.

## Privacy

The raw export includes IP addresses, devices and a timestamp for every play. The playlist CSVs include friends' Spotify IDs and personal playlist names. All of those files are listed in `.gitignore` and never committed. The published `data.json` contains only totals by song and month.

## Run it yourself

Request your Extended Streaming History from Spotify's privacy settings and put the `Streaming_History_Audio_*.json` files in this folder. Then run:

```sh
python3 build-dashboard.py              # writes dashboard/data.json
python3 -m http.server -d dashboard     # open http://localhost:8000
```

The page has to be served over HTTP, as above, because browsers block it from loading `data.json` when you open `index.html` directly from disk.

Pushing to `main` redeploys the site through GitHub Pages (see `.github/workflows/pages.yml`).

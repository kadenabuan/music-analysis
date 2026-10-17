# Listening Years

An interactive dashboard of three years of my Spotify listening history, from August 2023 to September 2026.

**Live site:** _coming soon_

## What it shows

- **Listening over time:** average minutes per day, by month or by year
- **Top artists and songs:** ranked by listening time or by number of plays
- **When I listen:** a weekday-by-hour heatmap of average listening
- **Artist lookup:** any artist's monthly listening and their top songs

A date-range filter at the top applies to every view.

## How it works

1. Spotify's [Extended Streaming History](https://www.spotify.com/account/privacy/) export provides one JSON row per play.
2. `build-dashboard.py` reads the audio files and converts UTC timestamps to local time. It then sums everything into totals by song and month, by day, and by weekday and hour, and writes `dashboard/data.json`.
3. `dashboard/index.html` loads that file and draws the charts in the browser with [Chart.js](https://www.chartjs.org/).

A play counts once it reaches 30 seconds, the same rule Spotify uses for a stream. Listening time includes every second played.

`spotify-analysis.py` is the original command-line version, which prints the same summaries as text.

## Privacy

The raw export includes IP addresses, devices and a timestamp for every play. Those files are listed in `.gitignore` and never committed. The published `data.json` contains only totals by song and month.

## Run it yourself

Request your Extended Streaming History from Spotify's privacy settings and put the `Streaming_History_Audio_*.json` files in this folder. Then run:

```sh
python3 build-dashboard.py              # writes dashboard/data.json
python3 -m http.server -d dashboard     # open http://localhost:8000
```

The page has to be served over HTTP, as above, because browsers block it from loading `data.json` when you open `index.html` directly from disk.

Pushing to `main` redeploys the site through GitHub Pages (see `.github/workflows/pages.yml`).

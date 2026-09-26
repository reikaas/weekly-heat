#!/usr/bin/env python3
"""Weekly Heat static site generator.

Reads data/weeks.json and regenerates:
  - index.html            (latest week + "Previous weeks")
  - week/YYYY-MM-DD.html  (one page per week)
  - archive.html          (every week, newest first)

Usage:  python3 build.py
No dependencies beyond the Python 3 standard library. Output is plain static
HTML (no client-side fetch), so the site works from file:// and GitHub Pages.

Adding a new Friday: add a week object to data/weeks.json (any position; the
newest date is treated as latest), then run this script.
"""
import html
import json
import os
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "weeks.json")
PREVIOUS_ON_INDEX = 4  # how many older weeks to list at the bottom of index.html

PLAY_SVG = ('<svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor">'
            '<path d="M8 5.14v13.72L19 12 8 5.14z"/></svg>')


def e(s):
    return html.escape(str(s), quote=True)


def label_for(week):
    if week.get("label"):
        return week["label"]
    d = date.fromisoformat(week["date"])
    return f"{d.day} {d.strftime('%b %Y')}"


def load():
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    weeks = sorted(data["weeks"], key=lambda w: w["date"], reverse=True)
    for w in weeks:
        w.setdefault("id", w["date"])
        w["label"] = label_for(w)
        w["tracks"] = sorted(w.get("tracks", []), key=lambda t: t["rank"])
    return data, weeks


def head(title, description, prefix):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{e(description)}">
  <title>{e(title)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{prefix}assets/styles.css">
</head>
"""


def header(data, prefix, current, skip_target="#tracks", skip_text="Skip to tracks"):
    def nav(href, text, key):
        cur = ' aria-current="page"' if current == key else ""
        return f'<li><a href="{href}"{cur}>{text}</a></li>'
    return f"""<body>
  <a class="skip-link" href="{skip_target}">{skip_text}</a>
  <header class="site-header">
    <div class="wrap header-row">
      <div class="brand">
        <p class="wordmark"><a href="{prefix}index.html">{e(data.get("site", "Weekly Heat"))}</a></p>
        <p class="tagline">{e(data.get("tagline", ""))}</p>
      </div>
      <nav aria-label="Primary">
        <ul class="nav-links">
          {nav(prefix + "index.html", "Latest", "latest")}
          {nav(prefix + "archive.html", "Archive", "archive")}
        </ul>
      </nav>
    </div>
  </header>
"""


def footer(data, prefix, note):
    return f"""
  <footer class="site-footer">
    <div class="wrap">
      <p>Sources: {e(data.get("sources", ""))}. Updated {e(data.get("updated", "Fridays"))} · {e(note)}</p>
      <p class="credit">Weekly Heat · Robin Eikaas · <span id="year">{date.today().year}</span></p>
    </div>
  </footer>
  <script src="{prefix}assets/site.js" defer></script>
</body>
</html>
"""


import re as _re


def yt_id(url):
    m = _re.search(r"(?:v=|youtu\.be/)([\w-]{11})", url or "")
    return m.group(1) if m else None


def ytm_url(url):
    vid = yt_id(url)
    return f"https://music.youtube.com/watch?v={vid}" if vid else url


def play_all_url(w):
    ids = [yt_id(t.get("youtube")) for t in w["tracks"]]
    ids = [i for i in ids if i]
    return "https://www.youtube.com/watch_videos?video_ids=" + ",".join(ids) if ids else None


def track_row(t):
    name = f'{t["artists"]} — {t["title"]}'
    lane = f' · <span class="trk-lane">{e(t["lane"])}</span>' if t.get("lane") else ""
    blurb = f'\n          <p class="trk-blurb">{e(t["blurb"])}</p>' if t.get("blurb") else ""
    play = ""
    if t.get("youtube"):
        play = (f'\n        <a class="trk-play" href="{e(ytm_url(t["youtube"]))}" target="_blank" rel="noopener noreferrer" '
                f'aria-label="Play {e(name)} on YouTube Music" title="Play on YouTube Music">{PLAY_SVG}</a>')
    return f"""      <li class="trk" id="track-{t["rank"]}">
        <span class="trk-rank" aria-label="Rank {t["rank"]}">{t["rank"]}</span>
        <div class="trk-main">
          <p class="trk-line"><span class="trk-artists">{e(t["artists"])}</span><span class="trk-sep"> — </span><span class="trk-title">{e(t["title"])}</span> <span class="trk-meta">{e(t.get("label", ""))}{lane}</span></p>{blurb}
        </div>{play}
      </li>"""


def week_link(prefix, w):
    return f'{prefix}week/{w["id"]}.html'


def teaser(w, n=3):
    return " · ".join(f'{t["artists"]} — {t["title"]}' for t in w["tracks"][:n])


def render_week(data, weeks, w, is_index):
    prefix = "" if is_index else "../"
    latest = weeks[0]
    is_latest = w is latest
    n = len(w["tracks"])
    if is_index:
        title = f'Weekly Heat — {data.get("tagline", "")}'
        badge = "Out now"
        current = "latest"
    else:
        title = f'Weekly Heat — {w["label"]}'
        badge = "Latest" if is_latest else "Archive"
        current = "latest" if is_latest else None
    desc = f'Weekly Heat — {w["label"]} house & techno club digs. {n} tracks with why-it-matters.'
    rows = "\n".join(track_row(t) for t in w["tracks"])
    pa = play_all_url(w)
    playall_html = (f'\n      <p class="hero-actions"><a class="play-all" href="{e(pa)}" target="_blank" rel="noopener noreferrer">{PLAY_SVG} Play all {n}</a></p>' if pa else "")

    # Previous / more weeks strip
    others = [x for x in weeks if x is not w][:PREVIOUS_ON_INDEX]
    items = []
    for x in others:
        href = f"{prefix}index.html" if (x is latest) else week_link(prefix, x)
        pill = '<span class="pill">Latest</span>' if x is latest else f'<span class="muted">{len(x["tracks"])} tracks</span>'
        items.append(f'        <li><a href="{href}"><span>{e(x["label"])}</span>{pill}</a></li>')
    items.append(f'        <li><a class="all-weeks" href="{prefix}archive.html"><span>All weeks in the archive</span><span aria-hidden="true">→</span></a></li>')
    heading = "Previous weeks" if is_index else "More weeks"

    body = f"""
  <main>
    <section class="hero wrap">
      <p class="hero-top"><span class="hero-badge">{badge}</span><span class="hero-date">{e(w["label"])}</span><span class="hero-count">{n} tracks</span></p>
      <p class="hero-scene">{e(w.get("scene", ""))}</p>{playall_html}
      <p class="hero-meta">{e(w.get("sourcesNote", ""))} <span class="kb-hint">Keys: <kbd>j</kbd>/<kbd>k</kbd> to step through play links.</span></p>
    </section>

    <section class="wrap" aria-label="{n} editorial digs">
      <ol class="tracklist" id="tracks">
{rows}
      </ol>
    </section>

    <section class="prev-weeks wrap" id="previous" aria-labelledby="prev-heading">
      <h2 id="prev-heading">{heading}</h2>
      <ul class="week-links">
{chr(10).join(items)}
      </ul>
    </section>
  </main>
"""
    note = "Latest dig" if is_latest else "Archive dig"
    return head(title, desc, prefix) + header(data, prefix, current) + body + footer(data, prefix, note)


def render_archive(data, weeks):
    latest = weeks[0]
    rows = []
    for w in weeks:
        pill = ' <span class="pill">Latest</span>' if w is latest else ""
        rows.append(f"""      <li class="arc-row">
        <a class="arc-link" href="{week_link("", w)}">
          <span class="arc-head"><span class="arc-date">{e(w["label"])}</span>{pill}<span class="arc-count">{len(w["tracks"])} tracks</span></span>
          <span class="arc-teaser">{e(teaser(w))}</span>
        </a>
      </li>""")
    body = f"""
  <main>
    <section class="hero wrap">
      <p class="hero-top"><span class="hero-badge">Archive</span><span class="hero-date">Every week</span><span class="hero-count">{len(weeks)} weeks</span></p>
      <p class="hero-scene">Every Weekly Heat dig, newest first. Top three tracks shown as a teaser.</p>
    </section>

    <section class="wrap" aria-label="All weeks">
      <ol class="archive-rows" id="weeks">
{chr(10).join(rows)}
      </ol>
    </section>
  </main>
"""
    return (head("Weekly Heat — Archive", "Every Weekly Heat house & techno dig, newest first.", "")
            + header(data, "", "archive", "#weeks", "Skip to weeks") + body
            + footer(data, "", "Archive"))


def write(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("wrote", rel)


def main():
    data, weeks = load()
    if not weeks:
        raise SystemExit("no weeks in data/weeks.json")
    write("index.html", render_week(data, weeks, weeks[0], True))
    for w in weeks:
        write(f"week/{w['id']}.html", render_week(data, weeks, w, False))
    write("archive.html", render_archive(data, weeks))
    nj = os.path.join(ROOT, ".nojekyll")
    if not os.path.exists(nj):
        write(".nojekyll", "\n")


if __name__ == "__main__":
    main()

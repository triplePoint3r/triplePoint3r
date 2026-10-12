import argparse
import datetime
import html
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path


def get_data(username):
    url = (
        "https://tryhackme.com/api/v2/public-profile?username="
        + urllib.parse.quote(username)
    )
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=18) as response:
        data = json.load(response)

    if not isinstance(data, dict):
        raise ValueError("Unexpected API response")

    return data.get("data", data)


def pick(data, *names):
    for name in names:
        value = data.get(name)
        if value is not None and value != "":
            return value
    return None


def render(username, data=None, error=None):
    data = data or {}
    user = data.get("user", data)
    if not isinstance(user, dict):
        user = data

    rank = pick(user, "rank", "globalRank", "worldRank")
    rooms = pick(user, "roomsCompleted", "completedRooms", "rooms")
    points = pick(user, "points", "totalPoints")
    level = pick(user, "level", "userLevel")

    def display(value):
        if value is None:
            return "—"
        if isinstance(value, (int, float)):
            return f"{value:,}"
        if isinstance(value, dict):
            return "—"
        return str(value)[:18]

    values = [
        ("WORLD RANK", rank),
        ("ROOMS", rooms),
        ("POINTS", points),
        ("LEVEL", level),
    ]

    boxes = []
    for index, (label, value) in enumerate(values):
        x = 30 + index * 183
        boxes.append(
            f'<rect x="{x}" y="145" width="171" height="94" rx="11" '
            f'fill="#111c27" stroke="#29404b"/>'
            f'<text x="{x + 14}" y="174" fill="#8ca4b0" font-size="12" '
            f'letter-spacing="1.4">{label}</text>'
            f'<text x="{x + 14}" y="216" fill="#e5fff5" font-size="28" '
            f'font-weight="700">{html.escape(display(value))}</text>'
        )

    status = (
        "LIVE PROFILE DATA"
        if data and not error
        else "DATA UNAVAILABLE"
        if error
        else "AWAITING PROFILE USERNAME"
    )
    status_color = "#4adea2" if data and not error else "#ffbd69"
    date = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M UTC"
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="300"
 viewBox="0 0 800 300" role="img"
 aria-label="TryHackMe profile card for {html.escape(username)}">
<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#0c1520"/>
<stop offset="1" stop-color="#101f2a"/></linearGradient>
<linearGradient id="accent"><stop stop-color="#35e5aa"/>
<stop offset="1" stop-color="#1ba5cb"/></linearGradient></defs>
<rect width="800" height="300" rx="18" fill="url(#bg)"/>
<rect x="1" y="1" width="798" height="298" rx="17" fill="none" stroke="#2d515b"/>
<rect x="0" y="0" width="7" height="300" rx="3" fill="url(#accent)"/>
<g font-family="Consolas,DejaVu Sans Mono,monospace">
<text x="30" y="38" fill="#48e6b2" font-size="13" letter-spacing="2">
// TRYHACKME • OPERATIVE PROFILE</text>
<text x="30" y="90" fill="#f0fff9" font-size="34" font-weight="700">
{html.escape(username[:28])}</text>
<text x="31" y="119" fill="#83a4ae" font-size="14">
CYBERSECURITY LEARNING / CTF / BLUE TEAM</text>
<rect x="596" y="28" width="173" height="30" rx="15" fill="#193039"/>
<circle cx="613" cy="43" r="5" fill="{status_color}"/>
<text x="628" y="47" fill="{status_color}" font-size="10">{status}</text>
{''.join(boxes)}
<path d="M30 257 H770" stroke="#29404b"/>
<text x="30" y="281" fill="#8ca4b0" font-size="12">
triplePoint3r / THM INTELLIGENCE CARD</text>
<text x="769" y="281" text-anchor="end" fill="#7c9ca7" font-size="11">
UPDATED {date}</text></g></svg>'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default=os.getenv("THM_USERNAME", "0xKernal"))
    parser.add_argument("--output", default="assets/tryhackme-card.svg")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        data = get_data(args.username)
    except Exception as exc:
        print(f"TryHackMe API unavailable: {exc}")

        # Keep the last known-good card instead of replacing real stats with
        # an unavailable/empty card when TryHackMe rate-limits the request.
        if output.exists() and output.stat().st_size > 0:
            print(f"Keeping existing card (last known version): {output}")
            return

        # No previous card exists yet, so create a clearly marked fallback.
        output.write_text(
            render(args.username, error=str(exc)),
            encoding="utf-8",
        )
        print(f"Generated fallback card: {output}")
        return

    output.write_text(render(args.username, data), encoding="utf-8")
    print(f"Generated {output} with fresh TryHackMe data")


if __name__ == "__main__":
    main()

"""
Baixa openfootball e gera CSVs flat para o Stage Snowflake.

- Big 5 2023/24 (football.json): partidas
- Copa 2022 (worldcup.more): partidas + gols com minuto

Saida: ./data_flat/ (matches_bronze.csv, goals_bronze.csv, league_catalog.csv)
"""

from __future__ import annotations

import csv
import json
import re
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / "data_flat"
OUT.mkdir(exist_ok=True)

SEASON_LEAGUES = "2023-24"
LEAGUES = {
    "en.1.json": ("EN", "English Premier League"),
    "es.1.json": ("ES", "Spanish La Liga"),
    "it.1.json": ("IT", "Italian Serie A"),
    "de.1.json": ("DE", "German Bundesliga"),
    "fr.1.json": ("FR", "French Ligue 1"),
}

FOOTBALL_JSON_BASE = (
    "https://raw.githubusercontent.com/openfootball/football.json/master"
)
WORLDCUP_TXT_URL = (
    "https://raw.githubusercontent.com/openfootball/worldcup.more/"
    "master/worldcup/2022_worldcup.txt"
)

SCORER_RE = re.compile(
    r"(?P<player>[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ.'\-]*(?:\s+[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ.'\-]*)*)"
    r"\s+"
    r"(?P<minute>\d+(?:\+\d+)?)"
    r"(?:"
    r"'\((?P<flag_paren>[^)]+)\)"
    r"|"
    r"'(?P<flag_suffix>p|og)?"
    r"|"
    r"(?P<flag_bare>p|og)"
    r")?",
    re.IGNORECASE,
)


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "di-p-openfootball/1.0"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return resp.read().decode("utf-8")


def fetch_json(url: str) -> dict:
    return json.loads(fetch_text(url))


def make_match_id(league_code: str, season: str, match_date: str, home: str, away: str) -> str:
    def norm(s: str) -> str:
        return re.sub(r"\s+", " ", (s or "").strip().upper())

    return "|".join([league_code, season, match_date or "", norm(home), norm(away)])


def minute_to_int(minute_raw: str) -> int | None:
    """90+3 -> 93 para ordenacao; 45 -> 45."""
    if not minute_raw:
        return None
    m = re.match(r"^(\d+)(?:\+(\d+))?$", minute_raw.strip())
    if not m:
        return None
    base = int(m.group(1))
    extra = int(m.group(2) or 0)
    return base + extra


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"Escrito {path.name}: {len(rows)} linhas")


def flatten_league_matches() -> list[dict]:
    rows: list[dict] = []
    for filename, (league_code, league_label) in LEAGUES.items():
        url = f"{FOOTBALL_JSON_BASE}/{SEASON_LEAGUES}/{filename}"
        print(f"Baixando {url}")
        payload = fetch_json(url)
        league_name = payload.get("name") or league_label
        for m in payload.get("matches", []):
            score = m.get("score") or {}
            ht = score.get("ht") or [None, None]
            ft = score.get("ft") or [None, None]
            home = m.get("team1")
            away = m.get("team2")
            match_date = m.get("date")
            rows.append(
                {
                    "match_id": make_match_id(
                        league_code, SEASON_LEAGUES, match_date, home, away
                    ),
                    "season": SEASON_LEAGUES,
                    "league_code": league_code,
                    "league_name": league_name,
                    "matchday": m.get("round"),
                    "match_date": match_date,
                    "match_time": m.get("time"),
                    "home_team": home,
                    "away_team": away,
                    "home_score_ht": ht[0] if isinstance(ht, list) and len(ht) > 0 else None,
                    "away_score_ht": ht[1] if isinstance(ht, list) and len(ht) > 1 else None,
                    "home_score_ft": ft[0] if isinstance(ft, list) and len(ft) > 0 else None,
                    "away_score_ft": ft[1] if isinstance(ft, list) and len(ft) > 1 else None,
                    "source_file": filename,
                    "source_repo": "openfootball/football.json",
                    "has_goal_events": 0,
                }
            )
    return rows


def parse_scorer_side(side_text: str, team: str, opponent: str, meta: dict) -> list[dict]:
    events: list[dict] = []
    if not side_text or not side_text.strip():
        return events

    text = re.sub(r"\s+", " ", side_text.strip())
    for match in SCORER_RE.finditer(text):
        player = (match.group("player") or "").strip(" ,;")
        minute_token = match.group("minute")
        if not player or not minute_token:
            continue
        if player.lower() in {"v", "vs", "penalties", "sent"}:
            continue

        flag = (
            match.group("flag_paren")
            or match.group("flag_suffix")
            or match.group("flag_bare")
            or ""
        ).lower()
        minute_int = minute_to_int(minute_token)
        events.append(
            {
                **meta,
                "team": team,
                "opponent": opponent,
                "scorer": player,
                "minute": minute_int,
                "minute_raw": minute_token + (("'(" + flag + ")") if flag else "'"),
                "is_penalty": 1 if "p" in flag else 0,
                "is_own_goal": 1 if "og" in flag else 0,
            }
        )
    return events


def flatten_worldcup() -> tuple[list[dict], list[dict]]:
    """Retorna (matches, goal_events) da Copa 2022."""
    print(f"Baixando {WORLDCUP_TXT_URL}")
    text = fetch_text(WORLDCUP_TXT_URL)
    lines = text.splitlines()

    matches: list[dict] = []
    goals: list[dict] = []
    current_date_raw = None
    current_date_iso = None
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        date_m = re.match(
            r"^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+(\w+)/(\d+)\s+@",
            line,
        )
        if date_m:
            current_date_raw = line
            mon = {
                "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
                "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
                "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
            }.get(date_m.group(1), "01")
            day = date_m.group(2).zfill(2)
            # datas do TXT usam ano no trecho; fallback 2022
            year_m = re.search(r"20\d{2}", line)
            year = year_m.group(0) if year_m else "2022"
            current_date_iso = f"{year}-{mon}-{day}"
            i += 1
            continue

        # linhas sem ano no mesmo padrao (Mon Nov/21 @ ...)
        date_m2 = re.match(
            r"^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+(\w+)/(\d+)\s+@",
            line,
        )
        if date_m2 and "@" in line:
            current_date_raw = line
            mon = {
                "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
                "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
                "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
            }.get(date_m2.group(1), "01")
            day = date_m2.group(2).zfill(2)
            year_m = re.search(r"20\d{2}", line)
            year = year_m.group(0) if year_m else "2022"
            current_date_iso = f"{year}-{mon}-{day}"
            i += 1
            continue

        score_m = re.match(
            r"^\s*(.+?)\s+v\s+(.+?)\s+(\d+)-(\d+)\b",
            line,
        )
        if score_m and current_date_iso:
            home = score_m.group(1).strip()
            away = score_m.group(2).strip()
            home_ft = int(score_m.group(3))
            away_ft = int(score_m.group(4))
            match_id = make_match_id("WC", "2022", current_date_iso, home, away)

            matches.append(
                {
                    "match_id": match_id,
                    "season": "2022",
                    "league_code": "WC",
                    "league_name": "FIFA World Cup 2022",
                    "matchday": None,
                    "match_date": current_date_iso,
                    "match_time": None,
                    "home_team": home,
                    "away_team": away,
                    "home_score_ht": None,
                    "away_score_ht": None,
                    "home_score_ft": home_ft,
                    "away_score_ft": away_ft,
                    "source_file": "2022_worldcup.txt",
                    "source_repo": "openfootball/worldcup.more",
                    "has_goal_events": 1,
                }
            )

            scorers_home = ""
            scorers_away = ""
            j = i + 1
            scorer_lines: list[str] = []
            while j < len(lines):
                nxt = lines[j].rstrip()
                if not nxt.strip():
                    if scorer_lines:
                        break
                    j += 1
                    continue
                if re.match(
                    r"^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\w+/\d+\s+@",
                    nxt,
                ):
                    break
                if re.match(r"^\s*.+\s+v\s+.+\s+\d+-\d+", nxt):
                    break
                if nxt.startswith("»") or nxt.startswith("="):
                    break
                if nxt.startswith("Penalties:") or nxt.startswith("Sent off:"):
                    break
                if re.match(r"^[A-Za-zÀ-ÿ].+:\s", nxt) and "Penalties" not in nxt:
                    if ":" in nxt and not re.search(r"\d+'", nxt):
                        break
                if re.search(r"\d+", nxt):
                    scorer_lines.append(nxt.strip())
                j += 1

            joined = " ".join(scorer_lines)
            if ";" in joined:
                parts = [p.strip() for p in joined.split(";", 1)]
                scorers_home = parts[0] if len(parts) > 0 else ""
                scorers_away = parts[1] if len(parts) > 1 else ""
            elif len(scorer_lines) >= 2:
                scorers_home = scorer_lines[0]
                scorers_away = scorer_lines[1]
            elif len(scorer_lines) == 1:
                if home_ft > 0 and away_ft == 0:
                    scorers_home = scorer_lines[0]
                elif away_ft > 0 and home_ft == 0:
                    scorers_away = scorer_lines[0]
                else:
                    scorers_home = scorer_lines[0]

            meta = {
                "match_id": match_id,
                "season": "2022",
                "league_code": "WC",
                "league_name": "FIFA World Cup 2022",
                "match_date": current_date_iso,
                "match_date_raw": current_date_raw,
                "home_team": home,
                "away_team": away,
                "home_score_ft": home_ft,
                "away_score_ft": away_ft,
                "source_file": "2022_worldcup.txt",
                "source_repo": "openfootball/worldcup.more",
            }
            goals.extend(parse_scorer_side(scorers_home, home, away, meta))
            goals.extend(parse_scorer_side(scorers_away, away, home, meta))
            i = j
            continue

        i += 1

    # sequencia dentro do match para desempate de minuto
    goals.sort(
        key=lambda g: (
            g["match_id"],
            g.get("minute") if g.get("minute") is not None else 999,
            g.get("scorer") or "",
        )
    )
    seq = 0
    prev = None
    for g in goals:
        if g["match_id"] != prev:
            seq = 0
            prev = g["match_id"]
        seq += 1
        g["event_seq"] = seq

    return matches, goals


def main() -> None:
    league_matches = flatten_league_matches()
    wc_matches, wc_goals = flatten_worldcup()
    matches = league_matches + wc_matches

    catalog = []
    seen = set()
    for m in matches:
        key = (m["league_code"], m["season"])
        if key in seen:
            continue
        seen.add(key)
        catalog.append(
            {
                "league_code": m["league_code"],
                "league_name": m["league_name"],
                "season": m["season"],
                "source_file": m["source_file"],
            }
        )

    match_fields = [
        "match_id", "season", "league_code", "league_name", "matchday",
        "match_date", "match_time", "home_team", "away_team",
        "home_score_ht", "away_score_ht", "home_score_ft", "away_score_ft",
        "source_file", "source_repo", "has_goal_events",
    ]
    goal_fields = [
        "match_id", "season", "league_code", "league_name", "match_date",
        "match_date_raw", "home_team", "away_team", "home_score_ft", "away_score_ft",
        "team", "opponent", "scorer", "minute", "minute_raw",
        "is_penalty", "is_own_goal", "event_seq",
        "source_file", "source_repo",
    ]
    cat_fields = ["league_code", "league_name", "season", "source_file"]

    write_csv(OUT / "matches_bronze.csv", matches, match_fields)
    write_csv(OUT / "goals_bronze.csv", wc_goals, goal_fields)
    write_csv(OUT / "league_catalog.csv", catalog, cat_fields)
    print(
        f"OK: matches={len(matches)} (ligas={len(league_matches)}, wc={len(wc_matches)}), "
        f"goals={len(wc_goals)}"
    )


if __name__ == "__main__":
    main()

"""
Baixa openfootball/worldcup.json (ZIP master) e gera CSVs flat para o Stage Snowflake.

Padrao alinhado ao Databricks (01_Pipeline_Football_Bronze):
- Fonte: https://github.com/openfootball/worldcup.json/archive/refs/heads/master.zip
- Filtro: name contem "World Cup" e nao contem "Club"
- match_id = MD5(match_date_team_home_team_away)
- Extração full do ZIP a cada run (sem janela de datas no codigo)

Saida: ./data_flat/matches_bronze.csv, goals_bronze.csv
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parent
OUT = BASE / "data_flat"
RAW = BASE / "data_raw" / "worldcup_json"
OUT.mkdir(exist_ok=True)
RAW.mkdir(parents=True, exist_ok=True)

ZIP_URL = (
    "https://github.com/openfootball/worldcup.json/archive/refs/heads/master.zip"
)


def fetch_bytes(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "di-p-worldcup/1.0"})
    with urlopen(req, timeout=120) as resp:
        return resp.read()


def make_match_id(match_date: str, team_home: str, team_away: str) -> str:
    key = f"{match_date}_{team_home}_{team_away}"
    return hashlib.md5(key.encode("utf-8")).hexdigest()


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"Escrito {path.name}: {len(rows)} linhas")


def is_world_cup(name: str) -> bool:
    n = name or ""
    return "World Cup" in n and "Club" not in n


def download_and_extract_zip() -> Path:
    print(f"Baixando {ZIP_URL}")
    payload = fetch_bytes(ZIP_URL)
    extract_root = RAW / "json_incremental" / "worldcup.json"
    if extract_root.exists():
        for p in sorted(extract_root.rglob("*"), reverse=True):
            if p.is_file():
                p.unlink()
            elif p.is_dir():
                p.rmdir()
    extract_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        zf.extractall(extract_root)
    print(f"ZIP extraido em {extract_root}")
    return extract_root


def iter_competition_json(root: Path):
    for path in sorted(root.rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Ignorando {path}: {exc}")
            continue
        if not isinstance(data, dict):
            continue
        name = data.get("name") or ""
        if not is_world_cup(name):
            continue
        matches = data.get("matches")
        if not matches:
            continue
        rel = str(path.relative_to(root)).replace("\\", "/")
        yield name, rel, matches


def flatten() -> None:
    root = download_and_extract_zip()
    match_rows: list[dict] = []
    goal_rows: list[dict] = []

    for competition_name, source_file, matches in iter_competition_json(root):
        for m in matches:
            if not isinstance(m, dict):
                continue
            score = m.get("score")
            ft = None
            ht = [None, None]
            if isinstance(score, dict):
                ft = score.get("ft")
                ht = score.get("ht") or [None, None]
            elif isinstance(score, list) and len(score) >= 2:
                # formatos antigos: score = [home, away]
                ft = score
            if not ft or len(ft) < 2 or ft[0] is None or ft[1] is None:
                continue

            match_date = m.get("date") or ""
            team_home = m.get("team1") or ""
            team_away = m.get("team2") or ""
            if not match_date or not team_home or not team_away:
                continue

            if not isinstance(ht, list):
                ht = [None, None]
            match_id = make_match_id(match_date, team_home, team_away)

            match_rows.append(
                {
                    "match_id": match_id,
                    "competition_name": competition_name,
                    "round": m.get("round"),
                    "match_date": match_date,
                    "match_time": m.get("time"),
                    "team_home": team_home,
                    "team_away": team_away,
                    "group_name": m.get("group"),
                    "ground": m.get("ground"),
                    "score_ft_home": ft[0],
                    "score_ft_away": ft[1],
                    "score_ht_home": ht[0] if len(ht) > 0 else None,
                    "score_ht_away": ht[1] if len(ht) > 1 else None,
                    "source_file": source_file,
                }
            )

            goals1 = m.get("goals1") or []
            goals2 = m.get("goals2") or []
            events = []
            for pos, g in enumerate(goals1):
                if not isinstance(g, dict):
                    continue
                events.append(
                    {
                        "pos": pos,
                        "team": team_home,
                        "opponent": team_away,
                        "scorer": g.get("name"),
                        "minute": g.get("minute"),
                        "is_penalty": 1 if g.get("penalty") else 0,
                        "is_own_goal": 1 if g.get("owngoal") else 0,
                    }
                )
            for pos, g in enumerate(goals2):
                if not isinstance(g, dict):
                    continue
                events.append(
                    {
                        "pos": pos,
                        "team": team_away,
                        "opponent": team_home,
                        "scorer": g.get("name"),
                        "minute": g.get("minute"),
                        "is_penalty": 1 if g.get("penalty") else 0,
                        "is_own_goal": 1 if g.get("owngoal") else 0,
                    }
                )

            events_sorted = sorted(
                events,
                key=lambda e: (
                    e["minute"] is None,
                    e["minute"] if e["minute"] is not None else 10**9,
                    e["pos"],
                ),
            )
            for seq, e in enumerate(events_sorted, start=1):
                goal_rows.append(
                    {
                        "match_id": match_id,
                        "competition_name": competition_name,
                        "match_date": match_date,
                        "team_home": team_home,
                        "team_away": team_away,
                        "score_ft_home": ft[0],
                        "score_ft_away": ft[1],
                        "source_file": source_file,
                        "team": e["team"],
                        "opponent": e["opponent"],
                        "scorer": e["scorer"],
                        "minute": e["minute"],
                        "is_penalty": e["is_penalty"],
                        "is_own_goal": e["is_own_goal"],
                        "event_seq": seq,
                    }
                )

    write_csv(
        OUT / "matches_bronze.csv",
        match_rows,
        [
            "match_id",
            "competition_name",
            "round",
            "match_date",
            "match_time",
            "team_home",
            "team_away",
            "group_name",
            "ground",
            "score_ft_home",
            "score_ft_away",
            "score_ht_home",
            "score_ht_away",
            "source_file",
        ],
    )
    write_csv(
        OUT / "goals_bronze.csv",
        goal_rows,
        [
            "match_id",
            "competition_name",
            "match_date",
            "team_home",
            "team_away",
            "score_ft_home",
            "score_ft_away",
            "source_file",
            "team",
            "opponent",
            "scorer",
            "minute",
            "is_penalty",
            "is_own_goal",
            "event_seq",
        ],
    )
    comps = sorted({r["competition_name"] for r in match_rows})
    print(f"Competicoes: {len(comps)}")
    for c in comps:
        print(f"  - {c}")


if __name__ == "__main__":
    flatten()

"""
Executa SQL no Snowflake a partir do .env (PAT/senha).
Uso:
    python run_snowflake_sql.py 01_setup_snowflake.sql
    python run_snowflake_sql.py --put-data-flat
    python run_snowflake_sql.py 02_bronze_ingest.sql
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from dotenv import dotenv_values
import snowflake.connector

ROOT = Path(__file__).resolve().parent


def connect():
    cfg = dotenv_values(ROOT / ".env")
    account = (cfg.get("SNOWFLAKE_ACCOUNT") or "").strip()
    user = (cfg.get("SNOWFLAKE_USER") or "").strip()
    password = (cfg.get("SNOWFLAKE_PAT") or cfg.get("SNOWFLAKE_PASSWORD") or "").strip()
    role = (cfg.get("SNOWFLAKE_ROLE") or "ACCOUNTADMIN").strip()
    warehouse = (cfg.get("SNOWFLAKE_WAREHOUSE") or "WH_DI_P_PIPELINE").strip()
    database = (cfg.get("SNOWFLAKE_DATABASE") or "DI_P_MEDALLION").strip()

    if not account or not user or not password:
        raise SystemExit("Preencha SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER e SNOWFLAKE_PAT no .env")

    conn = snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        role=role,
    )
    return conn, warehouse, database


def split_sql(text: str) -> list[str]:
    """Divide o script em statements, respeitando blocos $$."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    stmts: list[str] = []
    buf: list[str] = []
    in_dollar = False

    for raw in text.splitlines():
        line = raw
        stripped = line.strip()

        if not in_dollar and stripped.startswith("--"):
            continue

        if not in_dollar and "--" in line:
            line = line.split("--", 1)[0]

        if "$$" in line:
            count = line.count("$$")
            if count % 2 == 1:
                in_dollar = not in_dollar

        buf.append(line)

        if (not in_dollar) and line.rstrip().endswith(";"):
            stmt = "\n".join(buf).strip().rstrip(";").strip()
            if stmt:
                stmts.append(stmt)
            buf = []

    tail = "\n".join(buf).strip().rstrip(";").strip()
    if tail:
        stmts.append(tail)

    return stmts


def run_sql_file(path: Path) -> None:
    conn, warehouse, database = connect()
    cur = conn.cursor()
    try:
        print(f"==> Executando {path.name}")
        for i, stmt in enumerate(split_sql(path.read_text(encoding="utf-8")), 1):
            preview = " ".join(stmt.split())[:120]
            print(f"[{i}] {preview}")
            try:
                cur.execute(stmt)
                if cur.description:
                    rows = cur.fetchmany(20)
                    if rows:
                        cols = [d[0] for d in cur.description]
                        print("  cols:", cols)
                        for r in rows[:5]:
                            print("  ", r)
                        if len(rows) > 5:
                            print(f"  ... +{len(rows) - 5} rows")
                else:
                    print(f"  OK rowcount={cur.rowcount}")
            except Exception as e:
                print(f"  FAIL: {type(e).__name__}: {str(e)[:400]}")
                raise
        print(f"==> Concluido {path.name}")
    finally:
        cur.close()
        conn.close()


def put_data_flat() -> None:
    data_dir = ROOT / "data_flat"
    files = [
        data_dir / "matches_bronze.csv",
        data_dir / "goals_bronze.csv",
        data_dir / "league_catalog.csv",
    ]
    missing = [str(f) for f in files if not f.exists()]
    if missing:
        raise SystemExit(f"CSVs ausentes: {missing}. Rode 00_download_flatten_openfootball.py")

    conn, warehouse, database = connect()
    cur = conn.cursor()
    try:
        role = (dotenv_values(ROOT / ".env").get("SNOWFLAKE_ROLE") or "ACCOUNTADMIN")
        cur.execute(f"USE ROLE {role}")
        cur.execute(f"USE WAREHOUSE {warehouse}")
        cur.execute(f"USE DATABASE {database}")
        cur.execute("USE SCHEMA RAW")

        for f in files:
            local = str(f.resolve()).replace("\\", "/")
            sql = (
                f"PUT file://{local} @STG_OPENFOOTBALL "
                f"AUTO_COMPRESS=FALSE OVERWRITE=TRUE"
            )
            print(f"PUT {f.name} ...")
            cur.execute(sql)
            rows = cur.fetchall()
            print("  ", rows)

        cur.execute("LIST @STG_OPENFOOTBALL")
        print("LIST @STG_OPENFOOTBALL:")
        for r in cur.fetchall():
            print("  ", r[0], r[1] if len(r) > 1 else "")
    finally:
        cur.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("sql_file", nargs="?", help="Arquivo .sql para executar")
    parser.add_argument("--put-data-flat", action="store_true", help="Upload data_flat/*.csv no stage")
    args = parser.parse_args()

    if args.put_data_flat:
        put_data_flat()
    if args.sql_file:
        run_sql_file(ROOT / args.sql_file)
    if not args.put_data_flat and not args.sql_file:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

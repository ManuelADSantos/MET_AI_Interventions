#!/usr/bin/env python3
"""Dump Railway Postgres to a local SQL file."""
import subprocess, sys

# ponytail: paste your Railway public URL here, or pass as arg
DB_URL = sys.argv[1] if len(sys.argv) > 1 else "postgresql://user:pass@host:port/dbname"

subprocess.run(["pg_dump", DB_URL, "-f", "batch_2.sql"], check=True)
print("Done → backup.sql")
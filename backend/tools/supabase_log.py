"""
Optional: log NL queries to Supabase (Postgres) for "deployed database" requirement.
Set SUPABASE_URL and SUPABASE_ANON_KEY in env to enable.
Table: analytics_log (id, query, created_at)
"""

from __future__ import annotations

import os
import logging

logger = logging.getLogger("selma")

_SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
_SUPABASE_KEY = (os.getenv("SUPABASE_ANON_KEY") or "").strip()


def log_query(query: str) -> None:
    if not _SUPABASE_URL or not _SUPABASE_KEY:
        return
    try:
        import httpx
        resp = httpx.post(
            f"{_SUPABASE_URL}/rest/v1/analytics_log",
            json={"query": query[:2000]},
            headers={
                "apikey": _SUPABASE_KEY,
                "Authorization": f"Bearer {_SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            timeout=5,
        )
        if resp.status_code >= 400:
            logger.warning("Supabase log failed: %s %s", resp.status_code, resp.text)
    except Exception as e:
        logger.warning("Supabase log error: %s", e)

import json
import sqlite3
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DB_PATH = DATA_DIR / "construction_intelligence.db"


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS analyses (
            id TEXT PRIMARY KEY,
            module TEXT NOT NULL,
            title TEXT NOT NULL,
            project_name TEXT,
            location TEXT,
            risk_level TEXT,
            provider TEXT NOT NULL,
            created_at TEXT NOT NULL,
            result_json TEXT NOT NULL
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at DESC)")


def save_analysis(result: dict[str, Any]) -> None:
    with _connect() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO analyses
            (id, module, title, project_name, location, risk_level, provider, created_at, result_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                result["id"], result["module"], result["title"], result.get("project_name", ""),
                result.get("location", ""), result.get("risk_level", "Informational"),
                result.get("provider", "demo"), result["created_at"],
                json.dumps(result, ensure_ascii=False),
            ),
        )


def list_analyses(limit: int = 20) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 100))
    with _connect() as conn:
        rows = conn.execute("SELECT result_json FROM analyses ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return [json.loads(row["result_json"]) for row in rows]


def get_analysis(analysis_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute("SELECT result_json FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
    return json.loads(row["result_json"]) if row else None


def counts() -> dict[str, int]:
    with _connect() as conn:
        total = conn.execute("SELECT COUNT(*) AS n FROM analyses").fetchone()["n"]
        critical = conn.execute("SELECT COUNT(*) AS n FROM analyses WHERE risk_level IN ('High', 'Critical')").fetchone()["n"]
        recent = conn.execute("SELECT COUNT(*) AS n FROM analyses WHERE created_at >= datetime('now', '-7 days')").fetchone()["n"]
    return {"total_analyses": total, "high_risk_reports": critical, "analyses_last_7_days": recent}

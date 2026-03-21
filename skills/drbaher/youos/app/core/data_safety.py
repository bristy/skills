from __future__ import annotations

import json
import logging
import shutil
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import get_config_path
from app.core.settings import Settings
from app.db.bootstrap import bootstrap_database, resolve_schema_path, resolve_sqlite_path

_REQUIRED_TABLES = ("reply_pairs", "draft_history", "memory")
_RUNTIME_SCHEMA_REQUIREMENTS: dict[str, set[str]] = {
    "reply_pairs": {"id", "inbound_text", "reply_text", "auto_feedback_processed", "quality_score", "language"},
    "feedback_pairs": {
        "id",
        "generated_draft",
        "edited_reply",
        "edit_distance_pct",
        "reply_pair_id",
        "organic",
        "edit_categories",
        "precedents_used",
    },
    "draft_history": {"id", "generated_draft", "created_at"},
    "memory": {"id", "type", "key", "fact", "confidence"},
    "sender_profiles": {"id", "email", "avg_response_hours"},
    "review_streaks": {"id", "date", "review_count"},
    "exemplar_cache": {"cache_key", "source_ids_json"},
    "chunks_fts": set(),
    "reply_pairs_fts": set(),
}
_ESSENTIAL_CONFIG_FILES = (
    "persona.yaml",
    "prompts.yaml",
    "retrieval/defaults.yaml",
)

logger = logging.getLogger("youos.runtime")


@dataclass(slots=True)
class SafetyReport:
    db_path: str
    warnings: list[str]
    table_counts: dict[str, int]
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "db_path": self.db_path,
            "warnings": self.warnings,
            "table_counts": self.table_counts,
            "timestamp": self.timestamp,
        }


@dataclass(slots=True)
class RuntimeCheck:
    name: str
    status: str
    detail: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": self.status,
            "detail": self.detail,
        }
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload


def _is_unsafe_path(path: Path) -> bool:
    unsafe_parts = {".Trash", "Trash"}
    return any(part in unsafe_parts for part in path.parts)


def validate_instance_paths(settings: Settings) -> None:
    db_path = resolve_sqlite_path(settings.database_url).expanduser().resolve()
    if _is_unsafe_path(db_path):
        raise RuntimeError(f"Unsafe database path detected: {db_path}")

    if settings.data_dir is not None:
        data_dir = Path(settings.data_dir).expanduser().resolve()
        expected_db = (data_dir / "var" / "youos.db").resolve()
        if db_path != expected_db:
            raise RuntimeError(
                "Database path mismatch for instance mode: "
                f"expected {expected_db}, got {db_path}. "
                "Set YOUOS_DATABASE_URL to match YOUOS_DATA_DIR/var/youos.db."
            )
        if not data_dir.exists():
            raise RuntimeError(f"Instance data directory does not exist: {data_dir}")
        if not (data_dir / "var").exists():
            raise RuntimeError(f"Missing required directory: {data_dir / 'var'}")
        if not settings.configs_dir.exists():
            raise RuntimeError(f"Missing required configs directory: {settings.configs_dir}")


def _runtime_config_checks(settings: Settings, config: dict[str, Any] | None = None) -> dict[str, RuntimeCheck]:
    checks: dict[str, RuntimeCheck] = {}
    config_path = get_config_path()
    checks["config_file"] = RuntimeCheck(
        name="config_file",
        status="ok" if config_path.exists() else "fail",
        detail=f"Using config file at {config_path}" if config_path.exists() else f"Missing config file at {config_path}",
        metadata={"path": str(config_path)},
    )
    checks["configs_dir"] = RuntimeCheck(
        name="configs_dir",
        status="ok" if settings.configs_dir.exists() else "fail",
        detail=f"Configs directory ready at {settings.configs_dir}"
        if settings.configs_dir.exists()
        else f"Missing configs directory at {settings.configs_dir}",
        metadata={"path": str(settings.configs_dir)},
    )

    missing_files = [
        str(settings.configs_dir / rel_path)
        for rel_path in _ESSENTIAL_CONFIG_FILES
        if not (settings.configs_dir / rel_path).exists()
    ]
    checks["essential_configs"] = RuntimeCheck(
        name="essential_configs",
        status="ok" if not missing_files else "fail",
        detail="All essential config files are present." if not missing_files else "Missing essential config files.",
        metadata={"missing": missing_files},
    )

    schema_path = resolve_schema_path(settings)
    checks["schema_source"] = RuntimeCheck(
        name="schema_source",
        status="ok" if schema_path.exists() else "fail",
        detail=f"Schema source ready at {schema_path}" if schema_path.exists() else f"Schema source not found at {schema_path}",
        metadata={"path": str(schema_path)},
    )

    user_emails = tuple((config or {}).get("user", {}).get("emails", []))
    checks["user_identity"] = RuntimeCheck(
        name="user_identity",
        status="ok" if user_emails else "warn",
        detail="Configured user email identities detected."
        if user_emails
        else "No user emails configured yet; runtime is available but drafts may be less scoped.",
        metadata={"emails": list(user_emails)},
    )
    return checks


def _inspect_runtime_schema(db_path: Path) -> RuntimeCheck:
    if not db_path.exists():
        return RuntimeCheck(
            name="database_schema",
            status="fail",
            detail=f"Database file not found at {db_path}",
            metadata={"path": str(db_path)},
        )

    try:
        connection = sqlite3.connect(db_path)
    except Exception as exc:
        return RuntimeCheck(
            name="database_schema",
            status="fail",
            detail=f"Unable to open database: {exc}",
            metadata={"path": str(db_path)},
        )

    try:
        existing_tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')").fetchall()
        }
        missing_tables: list[str] = []
        missing_columns: dict[str, list[str]] = {}
        for table, required_columns in _RUNTIME_SCHEMA_REQUIREMENTS.items():
            if table not in existing_tables:
                missing_tables.append(table)
                continue
            if not required_columns:
                continue
            columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}
            absent = sorted(required_columns - columns)
            if absent:
                missing_columns[table] = absent
    finally:
        connection.close()

    if missing_tables or missing_columns:
        detail_parts: list[str] = []
        if missing_tables:
            detail_parts.append(f"missing tables: {', '.join(sorted(missing_tables))}")
        if missing_columns:
            formatted = ", ".join(
                f"{table}({', '.join(columns)})" for table, columns in sorted(missing_columns.items())
            )
            detail_parts.append(f"missing columns: {formatted}")
        return RuntimeCheck(
            name="database_schema",
            status="fail",
            detail="Schema is behind: " + "; ".join(detail_parts),
            metadata={
                "path": str(db_path),
                "missing_tables": sorted(missing_tables),
                "missing_columns": missing_columns,
            },
        )

    return RuntimeCheck(
        name="database_schema",
        status="ok",
        detail="Database schema is compatible with the current runtime.",
        metadata={"path": str(db_path)},
    )


def validate_startup_runtime(settings: Settings, config: dict[str, Any] | None = None) -> dict[str, Any]:
    validate_instance_paths(settings)
    db_path = resolve_sqlite_path(settings.database_url).expanduser().resolve()
    checks = _runtime_config_checks(settings, config)

    failures = [check.detail for check in checks.values() if check.status == "fail"]
    if failures:
        raise RuntimeError("Startup validation failed before database bootstrap: " + " | ".join(failures))

    schema_check = _inspect_runtime_schema(db_path)
    bootstrap_applied = False
    if schema_check.status != "ok":
        logger.warning("Database schema check failed at startup for %s: %s", db_path, schema_check.detail)
        schema_path = resolve_schema_path(settings)
        if not schema_path.exists():
            raise RuntimeError(
                f"Database schema is incompatible and bootstrap source is unavailable at {schema_path}: {schema_check.detail}"
            )
        logger.info("Attempting automatic bootstrap/migration using %s", schema_path)
        bootstrap_database(settings)
        bootstrap_applied = True
        schema_check = _inspect_runtime_schema(db_path)
        if schema_check.status != "ok":
            raise RuntimeError(
                "Automatic bootstrap completed but schema is still incompatible: "
                f"{schema_check.detail}"
            )

    checks["database"] = RuntimeCheck(
        name="database",
        status="ok",
        detail=f"Database ready at {db_path}",
        metadata={"path": str(db_path), "bootstrap_applied": bootstrap_applied},
    )
    checks["database_schema"] = schema_check

    safety_report = run_startup_safety_checks(settings)
    checks["startup_safety"] = RuntimeCheck(
        name="startup_safety",
        status="warn" if safety_report.warnings else "ok",
        detail="Startup safety checks completed with warnings."
        if safety_report.warnings
        else "Startup safety checks passed.",
        metadata={"warnings": list(safety_report.warnings), "table_counts": safety_report.table_counts},
    )

    warnings = [check.detail for check in checks.values() if check.status == "warn"]
    warnings.extend(safety_report.warnings)
    return {
        "db_path": str(db_path),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "bootstrap_applied": bootstrap_applied,
        "warnings": warnings,
        "checks": {name: check.to_dict() for name, check in checks.items()},
        "status": "ok" if not warnings else "degraded",
    }


def build_runtime_status(
    *,
    settings: Settings,
    config: dict[str, Any] | None,
    version: str,
    started_at_monotonic: float,
    readiness: bool,
    startup_report: dict[str, Any] | None,
    include_db_checks: bool,
) -> tuple[dict[str, Any], bool]:
    ready = readiness
    uptime_seconds = round(max(0.0, time.monotonic() - started_at_monotonic), 3)
    checks: dict[str, Any] = {
        "process": {
            "status": "ok",
            "detail": "Process is alive.",
        }
    }
    if startup_report:
        checks["startup"] = {
            "status": startup_report.get("status", "ok"),
            "detail": "Startup validation completed.",
            "metadata": {
                "bootstrap_applied": bool(startup_report.get("bootstrap_applied", False)),
                "warnings": startup_report.get("warnings", []),
            },
        }

    if include_db_checks:
        db_path = resolve_sqlite_path(settings.database_url).expanduser().resolve()
        checks.update({name: check.to_dict() for name, check in _runtime_config_checks(settings, config).items()})
        db_check = RuntimeCheck(
            name="database",
            status="ok",
            detail=f"Database reachable at {db_path}",
            metadata={"path": str(db_path)},
        )
        schema_check = _inspect_runtime_schema(db_path)
        if schema_check.status != "ok":
            db_check = RuntimeCheck(
                name="database",
                status="fail",
                detail=f"Database readiness failed for {db_path}",
                metadata={"path": str(db_path)},
            )
            ready = False
        checks["database"] = db_check.to_dict()
        checks["database_schema"] = schema_check.to_dict()
        if any(check.get("status") == "fail" for check in checks.values()):
            ready = False

    payload = {
        "status": "ok" if ready else "degraded",
        "version": version,
        "uptime_seconds": uptime_seconds,
        "ready": ready,
        "checks": checks,
    }
    return payload, ready


def _load_prev_counts(state_path: Path) -> dict[str, int]:
    if not state_path.exists():
        return {}
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
        return {str(k): int(v) for k, v in data.get("table_counts", {}).items()}
    except Exception:
        return {}


def run_startup_safety_checks(settings: Settings) -> SafetyReport:
    db_path = resolve_sqlite_path(settings.database_url).expanduser().resolve()
    warnings: list[str] = []
    counts: dict[str, int] = {}

    if not db_path.exists():
        warnings.append(f"Database file not found at startup: {db_path}")
    else:
        conn = sqlite3.connect(db_path)
        try:
            existing_tables = {
                row[0]
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            }
            for table in _REQUIRED_TABLES:
                if table not in existing_tables:
                    warnings.append(f"Required table missing: {table}")
                    counts[table] = 0
                    continue
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                counts[table] = int(count)
        finally:
            conn.close()

    var_dir = db_path.parent
    var_dir.mkdir(parents=True, exist_ok=True)
    state_path = var_dir / "startup_health_state.json"
    prev_counts = _load_prev_counts(state_path)

    for table in _REQUIRED_TABLES:
        prev = int(prev_counts.get(table, 0))
        curr = int(counts.get(table, 0))
        if prev > 0 and curr == 0:
            warnings.append(f"Regression detected: {table} dropped from {prev} to 0")

    timestamp = datetime.now(timezone.utc).isoformat()
    state_path.write_text(
        json.dumps({"timestamp": timestamp, "table_counts": counts}, indent=2),
        encoding="utf-8",
    )

    report = SafetyReport(
        db_path=str(db_path),
        warnings=warnings,
        table_counts=counts,
        timestamp=timestamp,
    )
    (var_dir / "startup_safety_report.json").write_text(
        json.dumps(report.to_dict(), indent=2),
        encoding="utf-8",
    )
    return report


def _snapshot_root(db_path: Path) -> Path:
    return db_path.parent / "snapshots"


def create_snapshot(db_path: Path, *, tier: str = "manual") -> Path:
    now = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_dir = _snapshot_root(db_path) / tier
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"youos-{now}.db"

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA wal_checkpoint(FULL)")
        backup_conn = sqlite3.connect(out_path)
        try:
            conn.backup(backup_conn)
        finally:
            backup_conn.close()
    finally:
        conn.close()

    return out_path


def prune_snapshots(db_path: Path, *, keep_hourly: int = 72, keep_daily: int = 30) -> None:
    root = _snapshot_root(db_path)
    for tier, keep in (("hourly", keep_hourly), ("daily", keep_daily), ("manual", 50)):
        tier_dir = root / tier
        if not tier_dir.exists():
            continue
        files = sorted(tier_dir.glob("youos-*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
        for old in files[keep:]:
            old.unlink(missing_ok=True)


def list_snapshots(db_path: Path) -> list[Path]:
    root = _snapshot_root(db_path)
    if not root.exists():
        return []
    files = sorted(root.glob("*/*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def restore_snapshot(db_path: Path, snapshot_path: Path, *, dry_run: bool = False) -> Path:
    if not snapshot_path.exists():
        raise FileNotFoundError(f"Snapshot not found: {snapshot_path}")

    backup_path = db_path.parent / f"youos.pre-restore-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.db"
    if dry_run:
        return backup_path

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        shutil.copy2(db_path, backup_path)
    shutil.copy2(snapshot_path, db_path)
    return backup_path

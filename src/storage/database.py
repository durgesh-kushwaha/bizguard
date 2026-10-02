"""
SQLite database module for BizGuard decision persistence.

Stores and retrieves decision contracts so they survive app restarts.
Uses SQLite for simplicity — no external database needed.
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Default database path
DB_PATH = Path(__file__).parent.parent.parent / "database" / "bizguard.db"


def _get_connection(db_path: Path = None) -> sqlite3.Connection:
    """Get a database connection, creating the database if needed."""
    if db_path is None:
        db_path = DB_PATH
    
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_database(db_path: Path = None):
    """
    Initialize the database schema.
    
    Creates the decisions table if it doesn't exist.
    Safe to call multiple times.
    """
    conn = _get_connection(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                decision_type TEXT NOT NULL,
                input_json TEXT,
                expected_outcome_json TEXT,
                scenario_results_json TEXT,
                assumptions_json TEXT,
                risks_json TEXT,
                monitoring_json TEXT,
                recommendation_json TEXT,
                user_notes TEXT,
                actual_outcome_json TEXT,
                status TEXT DEFAULT 'Simulated',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        logger.info("Database initialized successfully.")
    finally:
        conn.close()


def save_decision(contract: Dict, db_path: Path = None) -> str:
    """
    Save a decision contract to the database.
    
    Args:
        contract: Decision contract dict.
        db_path: Optional custom database path.
    
    Returns:
        Decision ID.
    """
    init_database(db_path)
    conn = _get_connection(db_path)
    
    try:
        decision_id = contract.get("decision_id", "")
        conn.execute("""
            INSERT OR REPLACE INTO decisions 
            (id, date, decision_type, input_json, expected_outcome_json,
             scenario_results_json, assumptions_json, risks_json,
             monitoring_json, recommendation_json, user_notes,
             actual_outcome_json, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            decision_id,
            contract.get("date", datetime.now().isoformat()),
            contract.get("decision_type", ""),
            json.dumps(contract.get("input", {})),
            json.dumps(contract.get("expected_outcome", {})),
            json.dumps(contract.get("scenario_results", {})),
            json.dumps(contract.get("key_assumptions", [])),
            json.dumps(contract.get("risk_indicators", [])),
            json.dumps(contract.get("monitoring_triggers", [])),
            json.dumps(contract.get("recommendation", {})),
            contract.get("user_notes", ""),
            json.dumps(contract.get("actual_outcome")),
            contract.get("status", "Simulated"),
        ))
        conn.commit()
        logger.info(f"Decision saved: {decision_id}")
        return decision_id
    finally:
        conn.close()


def get_all_decisions(db_path: Path = None) -> List[Dict]:
    """
    Retrieve all saved decisions.
    
    Returns:
        List of decision dicts, most recent first.
    """
    init_database(db_path)
    conn = _get_connection(db_path)
    
    try:
        cursor = conn.execute(
            "SELECT * FROM decisions ORDER BY created_at DESC"
        )
        rows = cursor.fetchall()
        
        decisions = []
        for row in rows:
            decision = {
                "decision_id": row["id"],
                "date": row["date"],
                "decision_type": row["decision_type"],
                "input": json.loads(row["input_json"] or "{}"),
                "expected_outcome": json.loads(row["expected_outcome_json"] or "{}"),
                "scenario_results": json.loads(row["scenario_results_json"] or "{}"),
                "key_assumptions": json.loads(row["assumptions_json"] or "[]"),
                "risk_indicators": json.loads(row["risks_json"] or "[]"),
                "monitoring_triggers": json.loads(row["monitoring_json"] or "[]"),
                "recommendation": json.loads(row["recommendation_json"] or "{}"),
                "user_notes": row["user_notes"],
                "actual_outcome": json.loads(row["actual_outcome_json"] or "null"),
                "status": row["status"],
            }
            decisions.append(decision)
        
        return decisions
    finally:
        conn.close()


def get_decision_by_id(decision_id: str, db_path: Path = None) -> Optional[Dict]:
    """
    Retrieve a single decision by ID.
    
    Args:
        decision_id: The decision ID.
    
    Returns:
        Decision dict, or None if not found.
    """
    decisions = get_all_decisions(db_path)
    for d in decisions:
        if d["decision_id"] == decision_id:
            return d
    return None


def update_actual_outcome(decision_id: str, actual_outcome: Dict,
                          db_path: Path = None):
    """
    Update a decision with the actual outcome for comparison.
    
    Args:
        decision_id: The decision ID.
        actual_outcome: Dict with actual results.
    """
    init_database(db_path)
    conn = _get_connection(db_path)
    
    try:
        conn.execute("""
            UPDATE decisions 
            SET actual_outcome_json = ?, status = 'Completed'
            WHERE id = ?
        """, (json.dumps(actual_outcome), decision_id))
        conn.commit()
        logger.info(f"Actual outcome updated for decision: {decision_id}")
    finally:
        conn.close()


def delete_decision(decision_id: str, db_path: Path = None):
    """Delete a decision by ID."""
    init_database(db_path)
    conn = _get_connection(db_path)
    
    try:
        conn.execute("DELETE FROM decisions WHERE id = ?", (decision_id,))
        conn.commit()
        logger.info(f"Decision deleted: {decision_id}")
    finally:
        conn.close()


def get_decision_count(db_path: Path = None) -> int:
    """Get the total number of saved decisions."""
    init_database(db_path)
    conn = _get_connection(db_path)
    
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM decisions")
        return cursor.fetchone()[0]
    finally:
        conn.close()

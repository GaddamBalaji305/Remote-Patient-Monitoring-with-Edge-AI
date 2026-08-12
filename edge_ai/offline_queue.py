import sqlite3
import json
import os
import datetime
from typing import List, Dict, Any, Optional

DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
DB_PATH = os.path.join(DB_DIR, "offline_queue.db")

class OfflineQueue:
    """
    SQLite-backed resilient offline store-and-forward queue for Edge AI events.
    Guarantees zero data loss when backend network connectivity is unavailable.
    """
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS offline_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    vitals_json TEXT NOT NULL,
                    prediction_json TEXT NOT NULL,
                    inference_latency REAL NOT NULL,
                    status TEXT DEFAULT 'QUEUED',
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def enqueue(
        self,
        patient_id: str,
        timestamp: str,
        vitals: Dict[str, Any],
        prediction: Dict[str, Any],
        inference_latency: float
    ) -> int:
        """Stores a telemetry and prediction event locally when offline."""
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        vitals_json = json.dumps(vitals)
        prediction_json = json.dumps(prediction)

        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO offline_events 
                (patient_id, timestamp, vitals_json, prediction_json, inference_latency, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'QUEUED', ?)
            """, (patient_id, timestamp, vitals_json, prediction_json, inference_latency, now_str))
            conn.commit()
            return cursor.lastrowid

    def get_pending_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves pending unsynchronized events ordered chronologically."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, patient_id, timestamp, vitals_json, prediction_json, inference_latency, status, created_at
                FROM offline_events
                WHERE status = 'QUEUED'
                ORDER BY id ASC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            
            events = []
            for r in rows:
                events.append({
                    "id": r["id"],
                    "patient_id": r["patient_id"],
                    "timestamp": r["timestamp"],
                    "vitals": json.loads(r["vitals_json"]),
                    "prediction": json.loads(r["prediction_json"]),
                    "inference_latency": r["inference_latency"],
                    "status": r["status"],
                    "created_at": r["created_at"]
                })
            return events

    def mark_synced(self, event_id: int):
        """Removes successfully synchronized events from local queue."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM offline_events WHERE id = ?", (event_id,))
            conn.commit()

    def get_queue_count(self) -> int:
        """Returns total number of pending queued events."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM offline_events WHERE status = 'QUEUED'")
            return cursor.fetchone()[0]

    def clear_queue(self):
        """Clears all events from local queue (used in testing)."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM offline_events")
            conn.commit()

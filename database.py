from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Any, Iterable, Iterator


class Database:
    def __init__(self, db_path: str = "points.db", timeout: float = 5.0):
        self._conn = sqlite3.connect(db_path, timeout=timeout)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")

    def close(self) -> None:
        self._conn.close()

    @contextmanager
    def transaction(self) -> Iterator[None]:
        try:
            self._conn.execute("BEGIN")
            yield
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def execute(self, sql: str, params: Iterable[Any] = ()) -> sqlite3.Cursor:
        cur = self._conn.cursor()
        cur.execute(sql, tuple(params))
        return cur

    def executemany(self, sql: str, seq_of_params: Iterable[Iterable[Any]]) -> sqlite3.Cursor:
        cur = self._conn.cursor()
        cur.executemany(sql, [tuple(p) for p in seq_of_params])
        return cur

    def fetchone(self, sql: str, params: Iterable[Any] = ()) -> sqlite3.Row | None:
        return self.execute(sql, params).fetchone()

    def fetchall(self, sql: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
        return self.execute(sql, params).fetchall()

    def insert(
        self,
        table: str,
        data: dict[str, Any],
        on_conflict: str | None = None,
    ) -> int:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        if on_conflict:
            sql = f"{sql} ON CONFLICT {on_conflict}"
        cur = self.execute(sql, data.values())
        self._conn.commit()
        return cur.lastrowid

    def update(
        self,
        table: str,
        data: dict[str, Any],
        where: str,
        params: Iterable[Any] = (),
    ) -> int:
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
        cur = self.execute(sql, [*data.values(), *params])
        self._conn.commit()
        return cur.rowcount

    def delete(self, table: str, where: str, params: Iterable[Any] = ()) -> int:
        sql = f"DELETE FROM {table} WHERE {where}"
        cur = self.execute(sql, params)
        self._conn.commit()
        return cur.rowcount

    def select(
        self,
        table: str,
        columns: str = "*",
        where: str | None = None,
        params: Iterable[Any] = (),
        order_by: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[sqlite3.Row]:
        sql = f"SELECT {columns} FROM {table}"
        if where:
            sql += f" WHERE {where}"
        if order_by:
            sql += f" ORDER BY {order_by}"
        if limit is not None:
            sql += f" LIMIT {limit}"
        if offset is not None:
            sql += f" OFFSET {offset}"
        return self.fetchall(sql, params)


class PointsRepository:
    def __init__(self, db: Database):
        self._db = db

    def ensure_schema(self) -> None:
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS points (user_id INTEGER PRIMARY KEY, points INTEGER)"
        )
        self._db._conn.commit()

    def ensure_user(self, user_id: int) -> None:
        self._db.insert(
            "points",
            {"user_id": user_id, "points": 0},
            on_conflict="(user_id) DO NOTHING",
        )

    def get_points(self, user_id: int) -> int | None:
        row = self._db.fetchone(
            "SELECT points FROM points WHERE user_id = ?",
            (user_id,),
        )
        return None if row is None else int(row["points"])

    def add_points(self, user_id: int, delta: int) -> int:
        with self._db.transaction():
            self.ensure_user(user_id)
            self._db.execute(
                "UPDATE points SET points = points + ? WHERE user_id = ?",
                (delta, user_id),
            )
            row = self._db.fetchone(
                "SELECT points FROM points WHERE user_id = ?",
                (user_id,),
            )
        return int(row["points"]) if row is not None else 0

    def top_rank(self, limit: int = 10) -> list[sqlite3.Row]:
        return self._db.select(
            "points",
            columns="user_id, points",
            order_by="points DESC",
            limit=limit,
        )

    def transfer(self, sender_id: int, recipient_id: int, points: int) -> bool:
        if points <= 0:
            return False
        with self._db.transaction():
            self.ensure_user(sender_id)
            self.ensure_user(recipient_id)
            row = self._db.fetchone(
                "SELECT points FROM points WHERE user_id = ?",
                (sender_id,),
            )
            sender_points = 0 if row is None else int(row["points"])
            if sender_points < points:
                return False
            self._db.execute(
                "UPDATE points SET points = points - ? WHERE user_id = ?",
                (points, sender_id),
            )
            self._db.execute(
                "UPDATE points SET points = points + ? WHERE user_id = ?",
                (points, recipient_id),
            )
        return True

    def award_point_for_message(self, user_id: int) -> int:
        return self.add_points(user_id, 1)

    def get_user_points(self, user_id: int) -> int | None:
        return self.get_points(user_id)

    def get_top_rank(self, limit: int = 10) -> list[sqlite3.Row]:
        return self.top_rank(limit)

    def send_points(self, sender_id: int, recipient_id: int, points: int) -> bool:
        return self.transfer(sender_id, recipient_id, points)

    def remove_points(self, admin_id: int, target_id: int, points: int) -> bool:
        return self.transfer(target_id, admin_id, points)

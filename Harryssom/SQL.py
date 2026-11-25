import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional

from entities import agenda as Agenda
from entities import person as Person

_DATABASE_PATH = Path(__file__).with_name("agenda.db")
_SCHEMA = """
CREATE TABLE IF NOT EXISTS person (
    id_person INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    phone INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS agenda (
    id INTEGER PRIMARY KEY,
    data TEXT NOT NULL,
    id_person INTEGER NOT NULL,
    FOREIGN KEY (id_person) REFERENCES person(id_person)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);
"""


@contextmanager
def _connection() -> Generator[sqlite3.Connection, None, None]:
    connection = sqlite3.connect(_DATABASE_PATH)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(_SCHEMA)
        with connection:
            yield connection
    finally:
        connection.close()


def create_person(value: Person) -> int:
    with _connection() as connection:
        connection.execute(
            "INSERT INTO person (id_person, name, phone) VALUES (?, ?, ?)",
            (value.id_person, value.name, value.phone),
        )
    return value.id_person


def read_person(id_person: int) -> Optional[Person]:
    with _connection() as connection:
        row = connection.execute(
            "SELECT id_person, name, phone FROM person WHERE id_person = ?",
            (id_person,),
        ).fetchone()
    if row is None:
        return None
    return Person(row["id_person"], row["name"], row["phone"])


def update_person(value: Person) -> bool:
    with _connection() as connection:
        cursor = connection.execute(
            "UPDATE person SET name = ?, phone = ? WHERE id_person = ?",
            (value.name, value.phone, value.id_person),
        )
    return cursor.rowcount > 0


def delete_person(id_person: int) -> bool:
    try:
        with _connection() as connection:
            cursor = connection.execute(
                "DELETE FROM person WHERE id_person = ?",
                (id_person,),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError(
            "Cannot delete a person while agenda entries reference them."
        ) from exc
    return cursor.rowcount > 0


def create_agenda(value: Agenda) -> int:
    with _connection() as connection:
        connection.execute(
            "INSERT INTO agenda (id, data, id_person) VALUES (?, ?, ?)",
            (value.id, value.data.isoformat(), value.id_person),
        )
    return value.id


def read_agenda(id: int) -> Optional[Agenda]:
    with _connection() as connection:
        row = connection.execute(
            "SELECT id, data, id_person FROM agenda WHERE id = ?",
            (id,),
        ).fetchone()
    if row is None:
        return None
    return Agenda(row["id"], datetime.fromisoformat(row["data"]), row["id_person"])


def update_agenda(value: Agenda) -> bool:
    with _connection() as connection:
        cursor = connection.execute(
            "UPDATE agenda SET data = ?, id_person = ? WHERE id = ?",
            (value.data.isoformat(), value.id_person, value.id),
        )
    return cursor.rowcount > 0


def delete_agenda(id: int) -> bool:
    with _connection() as connection:
        cursor = connection.execute("DELETE FROM agenda WHERE id = ?", (id,))
    return cursor.rowcount > 0

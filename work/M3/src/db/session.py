"""Connexion à la base DiagOps.

Le moteur par défaut est SQLite, suffisant pour le brief online et sans
installation. `DIAGOPS_DATABASE_URL` permet d'utiliser PostgreSQL sans modifier
le code.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = WORKSPACE_ROOT / "output" / "diagops.db"


def database_url() -> str:
    """Retourne l'URL de connexion, SQLite par défaut."""
    configured = os.environ.get("DIAGOPS_DATABASE_URL")
    if configured:
        return configured
    DEFAULT_DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite+pysqlite:///{DEFAULT_DATABASE_PATH}"


def build_engine(url: str | None = None, echo: bool = False) -> Engine:
    """Crée le moteur et active les clés étrangères sur SQLite.

    SQLite n'applique pas les clés étrangères par défaut : sans ce réglage, une
    contrainte déclarée dans le modèle n'a aucun effet à l'exécution. Vérifiez
    ce comportement avant de conclure qu'une contrainte fonctionne.
    """
    engine = create_engine(url or database_url(), echo=echo, future=True)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(connection, _record):  # pragma: no cover - I/O
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def build_session_factory(engine: Engine | None = None) -> sessionmaker[Session]:
    """Crée la fabrique de sessions attachée au moteur."""
    return sessionmaker(bind=engine or build_engine(), future=True)


@contextmanager
def session_scope(engine: Engine | None = None) -> Iterator[Session]:
    """Ouvre une session, valide à la sortie, annule en cas d'erreur."""
    factory = build_session_factory(engine)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

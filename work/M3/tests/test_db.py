from pathlib import Path

from sqlalchemy import select

from src.db.import_sources import import_equipment
from src.db.models import Base, Equipment
from src.db.session import build_engine, build_session_factory


HEADER = (
    "equipment_id,equipment_type,site_id,commissioning_date,criticality,"
    "manufacturer,rated_power_kw\n"
)


def prepared_csv(tmp_path: Path) -> Path:
    path = tmp_path / "equipment.csv"
    path.write_text(
        HEADER
        + "EQ-PUMP-001,pump,SITE-NORD,2014-03-02,critical,Rotatek,45.0\n"
        + "EQ-FAN-002,fan,SITE-SUD,,high,,\n"
        + "EQ-PUMP-001,pump,SITE-NORD,2014-03-02,critical,Rotatek,45.0\n",
        encoding="utf-8",
    )
    return path


def test_import_equipment_counts_inserted_and_rejected_rows(tmp_path: Path):
    engine = build_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = build_session_factory(engine)()

    report = import_equipment(session, prepared_csv(tmp_path))
    session.commit()

    assert report.read == 3
    assert report.inserted == 2
    assert report.rejected == 1
    assert sum(report.reasons.values()) == 1

    stored = session.scalars(select(Equipment)).all()
    assert {row.equipment_id for row in stored} == {"EQ-PUMP-001", "EQ-FAN-002"}
    assert next(row for row in stored if row.equipment_id == "EQ-FAN-002").manufacturer is None
    session.close()

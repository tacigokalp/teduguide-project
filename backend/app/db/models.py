"""Database tables as Python classes (SQLAlchemy 2).

One class = one table, one attribute = one column. Alembic reads this file to
write the migration scripts. Source: LLD section 3.1 (Figure 5) and Project.md A3.

Coordinates are metres on a flat floor plan, not latitude/longitude, so every
geometry uses SRID 0.
"""

from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Parent of every table class. `Base.metadata` is the list Alembic reads."""


# ---------------------------------------------------------------- campus data


class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True)  # "D"
    name: Mapped[str] = mapped_column(String(100))
    name_tr: Mapped[str | None] = mapped_column(String(100))
    side: Mapped[str | None] = mapped_column(String(20))
    color: Mapped[str | None] = mapped_column(String(20))
    # Angle between the floor plan's "up" and true north, used by the phone's compass.
    heading_offset_deg: Mapped[float] = mapped_column(Float, default=0.0, server_default="0")


class Floor(Base):
    __tablename__ = "floors"
    __table_args__ = (UniqueConstraint("building_id", "level"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    building_id: Mapped[int] = mapped_column(ForeignKey("buildings.id", ondelete="CASCADE"))
    level: Mapped[int] = mapped_column(Integer)  # ground floor = 0, range -2..5
    label: Mapped[str | None] = mapped_column(String(50))
    svg_url: Mapped[str | None] = mapped_column(String(300))
    geojson_url: Mapped[str | None] = mapped_column(String(300))
    width_m: Mapped[float | None] = mapped_column(Float)
    height_m: Mapped[float | None] = mapped_column(Float)
    meters_per_unit: Mapped[float | None] = mapped_column(Float)


class NavNode(Base):
    """A point of the walking map (corridor, door, stair, lift...)."""

    __tablename__ = "nav_nodes"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('corridor','junction','door','stair','elevator','entrance','connector')"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    floor_id: Mapped[int] = mapped_column(ForeignKey("floors.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(20))
    geom: Mapped[Any] = mapped_column(Geometry("POINT", srid=0))
    is_accessible: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    is_restricted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    # Stable name from the data files. Meant to be unique per building (checked in the
    # seed/import tool, because the building is only reachable through the floor).
    ref_code: Mapped[str | None] = mapped_column(String(50), index=True)


class NavEdge(Base):
    """A walkable line between two nodes."""

    __tablename__ = "nav_edges"
    __table_args__ = (CheckConstraint("kind IN ('walk','stairs','elevator','outdoor','ramp')"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    from_node: Mapped[int] = mapped_column(ForeignKey("nav_nodes.id", ondelete="CASCADE"))
    to_node: Mapped[int] = mapped_column(ForeignKey("nav_nodes.id", ondelete="CASCADE"))
    weight_m: Mapped[float] = mapped_column(Float)
    kind: Mapped[str] = mapped_column(String(20))
    is_accessible: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    is_restricted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    bidirectional: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    floors_spanned: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class Location(Base):
    """One room or place (classroom, office, lab, toilet...)."""

    __tablename__ = "locations"
    __table_args__ = (
        CheckConstraint(
            "type IN ('classroom','lab','amphi','studio','meeting','office','facility','wc')"
        ),
        # Typo-tolerant search: compares folded text in 3-letter pieces (pg_trgm).
        Index(
            "ix_locations_search_text_trgm",
            "search_text",
            postgresql_using="gin",
            postgresql_ops={"search_text": "gin_trgm_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    floor_id: Mapped[int] = mapped_column(ForeignKey("floors.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(30), unique=True)  # "D232"
    name: Mapped[str] = mapped_column(String(200))
    name_tr: Mapped[str | None] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(20))
    subtype: Mapped[str | None] = mapped_column(String(50))
    geom: Mapped[Any | None] = mapped_column(Geometry("POINT", srid=0))
    area: Mapped[Any | None] = mapped_column(Geometry("POLYGON", srid=0))
    door_node_id: Mapped[int | None] = mapped_column(ForeignKey("nav_nodes.id", ondelete="SET NULL"))
    is_accessible: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    opening_hours: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    search_text: Mapped[str] = mapped_column(Text, default="", server_default="")  # fold_tr(...)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Person(Base):
    __tablename__ = "people"
    __table_args__ = (
        Index(
            "ix_people_search_text_trgm",
            "search_text",
            postgresql_using="gin",
            postgresql_ops={"search_text": "gin_trgm_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200))
    title: Mapped[str | None] = mapped_column(String(50))
    role: Mapped[str | None] = mapped_column(String(100))
    department: Mapped[str | None] = mapped_column(String(200))
    faculty: Mapped[str | None] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(200))
    office_hours: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id", ondelete="SET NULL"))
    search_text: Mapped[str] = mapped_column(Text, default="", server_default="")  # fold_tr(...)


# ------------------------------------------------------------ WiFi positioning


class FingerprintPoint(Base):
    """A reference point on the floor plan where WiFi scans were taken."""

    __tablename__ = "fingerprint_points"

    id: Mapped[int] = mapped_column(primary_key=True)
    floor_id: Mapped[int] = mapped_column(ForeignKey("floors.id", ondelete="CASCADE"))
    x: Mapped[float] = mapped_column(Float)
    y: Mapped[float] = mapped_column(Float)
    label: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FingerprintSample(Base):
    """One raw WiFi scan at a reference point. The k-NN needs every raw scan."""

    __tablename__ = "fingerprint_samples"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    point_id: Mapped[int] = mapped_column(ForeignKey("fingerprint_points.id", ondelete="CASCADE"))
    device: Mapped[str | None] = mapped_column(String(100))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    vector: Mapped[dict[str, Any]] = mapped_column(JSONB)  # {bssid: rssi}
    source: Mapped[str | None] = mapped_column(String(30))  # "survey", "csv_import", "synthetic"...


class AccessPoint(Base):
    """A WiFi access point seen during surveys."""

    __tablename__ = "access_points"

    id: Mapped[int] = mapped_column(primary_key=True)
    bssid: Mapped[str] = mapped_column(String(17), unique=True)
    ssid: Mapped[str | None] = mapped_column(String(100))
    building_id: Mapped[int | None] = mapped_column(ForeignKey("buildings.id", ondelete="SET NULL"))
    floor_id: Mapped[int | None] = mapped_column(ForeignKey("floors.id", ondelete="SET NULL"))
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RadioMapVersion(Base):
    """A published WiFi map for one building. Only one version per building is active."""

    __tablename__ = "radio_map_versions"
    __table_args__ = (UniqueConstraint("building_id", "version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    building_id: Mapped[int] = mapped_column(ForeignKey("buildings.id", ondelete="CASCADE"))
    version: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)  # what the phone downloads
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSONB)  # accuracy numbers
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ----------------------------------------------------------------------- admin


class AdminUser(Base):
    __tablename__ = "admin_users"
    __table_args__ = (CheckConstraint("role IN ('editor','admin')"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))  # argon2, never the password
    role: Mapped[str] = mapped_column(String(10), default="editor", server_default="editor")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AdminRefreshToken(Base):
    __tablename__ = "admin_refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("admin_users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(128), unique=True)  # hash, never the token
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AdminAction(Base):
    """Audit log: who changed what and when."""

    __tablename__ = "admin_actions"

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[int | None] = mapped_column(ForeignKey("admin_users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(50))
    table_name: Mapped[str | None] = mapped_column(String(50))
    record_id: Mapped[int | None] = mapped_column(Integer)
    diff: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

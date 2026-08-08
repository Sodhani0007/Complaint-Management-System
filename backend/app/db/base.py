"""
Single declarative base every ORM model inherits from.

Why a separate file: if Base lived inside session.py, importing session.py
(to get a DB connection) would force-import every model too, risking circular
imports once models start referencing services. Keeping Base isolated breaks
that cycle.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

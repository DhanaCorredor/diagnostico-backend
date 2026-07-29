"""Helpers shared by the services."""

from sqlalchemy import func
from sqlalchemy.orm import Session


def normalized(value):
    """Lowercase and strip accents, so `MARÍA` and `maria` compare as the same text.

    Works both on a column and on a plain value, so the same expression can be used on
    each side of the comparison. `unaccent` comes from the extension of the same name.
    """
    return func.unaccent(func.lower(value))


def value_in_use(db: Session, model, column, value, exclude_id=None) -> bool:
    """True if a row of `model` with that `value` in `column` already exists (uniqueness check).

    The comparison ignores case and accents, so `Ecografía` and `ECOGRAFIA` count as the same
    name. With `exclude_id` that row is ignored, so it does not clash with itself when editing.
    """
    q = db.query(model).filter(normalized(column) == normalized(value))
    if exclude_id is not None:
        q = q.filter(model.id != exclude_id)
    return db.query(q.exists()).scalar()

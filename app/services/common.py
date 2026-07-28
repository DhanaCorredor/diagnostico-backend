"""Helpers shared by the services."""

from sqlalchemy.orm import Session


def value_in_use(db: Session, model, column, value, exclude_id=None) -> bool:
    """True if a row of `model` with that `value` in `column` already exists (uniqueness check).

    With `exclude_id` that row is ignored, so it does not clash with itself when editing.
    """
    q = db.query(model).filter(column == value)
    if exclude_id is not None:
        q = q.filter(model.id != exclude_id)
    return db.query(q.exists()).scalar()

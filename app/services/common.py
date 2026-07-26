"""Utilidades compartidas por los servicios."""

from sqlalchemy.orm import Session


def value_in_use(db: Session, model, column, value, exclude_id=None) -> bool:
    """True si ya existe una fila de `model` con ese `value` en `column` (chequeo de unicidad).

    Con `exclude_id` ignora esa fila, para no chocar consigo misma al editar.
    """
    q = db.query(model).filter(column == value)
    if exclude_id is not None:
        q = q.filter(model.id != exclude_id)
    return db.query(q.exists()).scalar()

"""Utilidades compartidas por los servicios."""

from sqlalchemy.orm import Session


def value_in_use(db: Session, modelo, columna, valor, excluir_id=None) -> bool:
    """True si ya existe una fila de `modelo` con ese `valor` en `columna` (chequeo de unicidad).

    Con `excluir_id` ignora esa fila, para no chocar consigo misma al editar.
    """
    q = db.query(modelo).filter(columna == valor)
    if excluir_id is not None:
        q = q.filter(modelo.id != excluir_id)
    return db.query(q.exists()).scalar()

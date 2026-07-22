"""Utilidades compartidas por los servicios."""

from sqlalchemy.orm import Session


def valor_en_uso(db: Session, modelo, columna, valor, excluir_id=None) -> bool:
    """True si ya existe una fila de `modelo` cuyo `columna` vale `valor`.

    Con `excluir_id` ignora esa fila (para no chocar consigo misma al editar).
    Centraliza el patrón de las reglas de unicidad (email, cédula, nombres únicos).
    """
    q = db.query(modelo).filter(columna == valor)
    if excluir_id is not None:
        q = q.filter(modelo.id != excluir_id)
    return db.query(q.exists()).scalar()

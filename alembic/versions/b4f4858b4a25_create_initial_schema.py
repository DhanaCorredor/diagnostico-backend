"""create initial schema

Revision ID: b4f4858b4a25
Revises: 
Create Date: 2026-07-13 09:09:48.282285

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b4f4858b4a25'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('especialidades',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('nombre', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nombre')
    )
    op.create_table('servicios',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('nombre', sa.String(), nullable=False),
    sa.Column('categoria', sa.Enum('CONSULTA', 'ECOGRAFIA', 'ESTUDIO_CARDIACO', 'OTRO', name='serviciocategoria'), nullable=False),
    sa.Column('duracion_min', sa.Integer(), nullable=False),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nombre')
    )
    op.create_table('usuarios',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('nombre_completo', sa.String(), nullable=False),
    sa.Column('rol', sa.Enum('ADMIN', 'RECEPCION', 'MEDICO', 'PACIENTE', name='rol'), nullable=False),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('password_hash', sa.String(), nullable=True),
    sa.Column('cedula', sa.String(), nullable=True),
    sa.Column('edad', sa.Integer(), nullable=True),
    sa.Column('fecha_nacimiento', sa.Date(), nullable=True),
    sa.Column('telefono', sa.String(), nullable=True),
    sa.Column('matricula', sa.String(), nullable=True),
    sa.Column('alergias', sa.Text(), nullable=True),
    sa.Column('antecedentes', sa.Text(), nullable=True),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('cedula'),
    sa.UniqueConstraint('email')
    )
    op.create_table('citas',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('paciente_id', sa.UUID(), nullable=False),
    sa.Column('medico_id', sa.UUID(), nullable=False),
    sa.Column('servicio_id', sa.UUID(), nullable=False),
    sa.Column('starts_at', sa.DateTime(), nullable=False),
    sa.Column('ends_at', sa.DateTime(), nullable=False),
    sa.Column('estado', sa.Enum('SCHEDULED', 'CONFIRMED', 'CANCELLED', 'COMPLETED', 'NO_SHOW', name='estadocita'), nullable=False),
    sa.Column('motivo', sa.String(), nullable=True),
    sa.Column('creado_por_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['creado_por_id'], ['usuarios.id'], ),
    sa.ForeignKeyConstraint(['medico_id'], ['usuarios.id'], ),
    sa.ForeignKeyConstraint(['paciente_id'], ['usuarios.id'], ),
    sa.ForeignKeyConstraint(['servicio_id'], ['servicios.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('disponibilidad',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('usuario_id', sa.UUID(), nullable=False),
    sa.Column('dia_semana', sa.Integer(), nullable=False),
    sa.Column('hora_inicio', sa.Time(), nullable=False),
    sa.Column('hora_fin', sa.Time(), nullable=False),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('usuario_especialidad',
    sa.Column('usuario_id', sa.UUID(), nullable=False),
    sa.Column('especialidad_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['especialidad_id'], ['especialidades.id'], ),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
    sa.PrimaryKeyConstraint('usuario_id', 'especialidad_id')
    )
    op.create_table('notas_clinicas',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('paciente_id', sa.UUID(), nullable=False),
    sa.Column('medico_id', sa.UUID(), nullable=False),
    sa.Column('cita_id', sa.UUID(), nullable=True),
    sa.Column('fecha', sa.DateTime(), nullable=False),
    sa.Column('contenido', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['cita_id'], ['citas.id'], ),
    sa.ForeignKeyConstraint(['medico_id'], ['usuarios.id'], ),
    sa.ForeignKeyConstraint(['paciente_id'], ['usuarios.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('notas_clinicas')
    op.drop_table('usuario_especialidad')
    op.drop_table('disponibilidad')
    op.drop_table('citas')
    op.drop_table('usuarios')
    op.drop_table('servicios')
    op.drop_table('especialidades')
    sa.Enum(name='rol').drop(op.get_bind())
    sa.Enum(name='estadocita').drop(op.get_bind())
    sa.Enum(name='serviciocategoria').drop(op.get_bind())

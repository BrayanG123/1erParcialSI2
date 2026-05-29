"""correcciones_base

Revision ID: b3c4d5e6f7a8
Revises: 49ec46f9fb8d
Create Date: 2026-05-25 00:00:00.000000

Cambios incluidos:
- Enum estado_asignacion: nuevos valores correctos
- Bitacora: agregar columna entidad_afectada
- HistorialEstado: hacer asignacion_id nullable, agregar incidente_id
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3c4d5e6f7a8'
down_revision = '49ec46f9fb8d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ===========================================================
    # PASO 1: Corregir el Enum estado_asignacion
    # ===========================================================
    # 1a. Convertir la columna a VARCHAR para poder modificarla libremente
    op.execute(
        "ALTER TABLE asignaciones_servicio "
        "ALTER COLUMN estado TYPE VARCHAR(50)"
    )

    # 1b. Eliminar el tipo ENUM viejo
    op.execute("DROP TYPE IF EXISTS estado_asignacion")

    # 1c. Mapear valores viejos → valores nuevos
    op.execute(
        "UPDATE asignaciones_servicio SET estado = 'taller_asignado' "
        "WHERE estado = 'aceptada'"
    )
    op.execute(
        "UPDATE asignaciones_servicio SET estado = 'en_atencion' "
        "WHERE estado = 'en_servicio'"
    )
    op.execute(
        "UPDATE asignaciones_servicio SET estado = 'finalizado' "
        "WHERE estado = 'completada'"
    )
    op.execute(
        "UPDATE asignaciones_servicio SET estado = 'cancelado' "
        "WHERE estado = 'cancelada'"
    )

    # 1d. Crear el nuevo tipo ENUM con los valores correctos
    op.execute(
        "CREATE TYPE estado_asignacion AS ENUM ("
        "    'pendiente', 'buscando_taller', 'taller_asignado', "
        "    'en_camino', 'en_atencion', 'finalizado', 'cancelado', 'rechazada'"
        ")"
    )

    # 1e. Volver a asignar el tipo ENUM a la columna
    op.execute(
        "ALTER TABLE asignaciones_servicio "
        "ALTER COLUMN estado TYPE estado_asignacion "
        "USING estado::estado_asignacion"
    )

    # ===========================================================
    # PASO 2: Agregar entidad_afectada a bitacora
    # ===========================================================
    op.add_column(
        "bitacora",
        sa.Column("entidad_afectada", sa.String(50), nullable=True)
    )

    # ===========================================================
    # PASO 3: Corregir historial_estados
    # ===========================================================
    # 3a. Hacer asignacion_id nullable
    op.alter_column(
        "historial_estados",
        "asignacion_id",
        existing_type=sa.Integer(),
        nullable=True
    )

    # 3b. Agregar incidente_id como FK nullable
    op.add_column(
        "historial_estados",
        sa.Column("incidente_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "fk_historial_incidente",       # nombre del constraint
        "historial_estados",            # tabla origen
        "incidentes",                   # tabla destino
        ["incidente_id"],               # columna origen
        ["id"],                         # columna destino
        ondelete="CASCADE"
    )


def downgrade() -> None:
    # ===========================================================
    # Revertir en orden inverso
    # ===========================================================

    # Revertir PASO 3
    op.drop_constraint("fk_historial_incidente", "historial_estados", type_="foreignkey")
    op.drop_column("historial_estados", "incidente_id")
    op.alter_column(
        "historial_estados",
        "asignacion_id",
        existing_type=sa.Integer(),
        nullable=False
    )

    # Revertir PASO 2
    op.drop_column("bitacora", "entidad_afectada")

    # Revertir PASO 1 (restaurar enum viejo)
    op.execute(
        "ALTER TABLE asignaciones_servicio "
        "ALTER COLUMN estado TYPE VARCHAR(50)"
    )
    op.execute("DROP TYPE IF EXISTS estado_asignacion")

    op.execute(
        "UPDATE asignaciones_servicio SET estado = 'aceptada' "
        "WHERE estado = 'taller_asignado'"
    )
    op.execute(
        "UPDATE asignaciones_servicio SET estado = 'en_servicio' "
        "WHERE estado = 'en_atencion'"
    )
    op.execute(
        "UPDATE asignaciones_servicio SET estado = 'completada' "
        "WHERE estado = 'finalizado'"
    )
    op.execute(
        "UPDATE asignaciones_servicio SET estado = 'cancelada' "
        "WHERE estado = 'cancelado'"
    )

    op.execute(
        "CREATE TYPE estado_asignacion AS ENUM ("
        "    'pendiente', 'aceptada', 'rechazada', "
        "    'en_camino', 'en_servicio', 'completada', 'cancelada'"
        ")"
    )
    op.execute(
        "ALTER TABLE asignaciones_servicio "
        "ALTER COLUMN estado TYPE estado_asignacion "
        "USING estado::estado_asignacion"
    )
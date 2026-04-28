"""fix_estadoincidente_enum: cambia valores a disponible/no_disponible

Revision ID: fix_estadoincidente_enum
Revises: e4de9bddafc6
Create Date: 2026-04-28

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'fix_estadoincidente_enum'
down_revision: Union[str, None] = 'e4de9bddafc6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Convertir la columna a texto para poder eliminar el enum
    op.execute("ALTER TABLE incidentes ALTER COLUMN estado TYPE VARCHAR(50)")

    # 2. Eliminar el enum antiguo
    op.execute("DROP TYPE IF EXISTS estadoincidente")

    # 3. Crear el nuevo enum con los valores correctos
    op.execute("CREATE TYPE estadoincidente AS ENUM ('disponible', 'no_disponible')")

    # 4. Migrar datos existentes: cualquier valor antiguo pasa a 'disponible'
    op.execute("UPDATE incidentes SET estado = 'disponible'")

    # 5. Volver a tipar la columna con el nuevo enum
    op.execute(
        "ALTER TABLE incidentes "
        "ALTER COLUMN estado TYPE estadoincidente "
        "USING estado::estadoincidente"
    )

    # 6. Restaurar el default y NOT NULL (por si acaso)
    op.execute(
        "ALTER TABLE incidentes "
        "ALTER COLUMN estado SET DEFAULT 'disponible'::estadoincidente"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE incidentes ALTER COLUMN estado TYPE VARCHAR(50)")
    op.execute("DROP TYPE IF EXISTS estadoincidente")
    op.execute(
        "CREATE TYPE estadoincidente AS ENUM "
        "('pendiente', 'asignado', 'en_camino', 'en_servicio', 'completado', 'cancelado')"
    )
    op.execute("UPDATE incidentes SET estado = 'pendiente'")
    op.execute(
        "ALTER TABLE incidentes "
        "ALTER COLUMN estado TYPE estadoincidente "
        "USING estado::estadoincidente"
    )

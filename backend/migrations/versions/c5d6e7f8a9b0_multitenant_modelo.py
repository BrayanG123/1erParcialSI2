"""multitenant_modelo

Revision ID: c5d6e7f8a9b0
Revises: b3c4d5e6f7a8
Create Date: 2026-05-27 00:00:00.000000

Cambios incluidos:
- Crear tabla tenants con enum plan_tenant
- Agregar tenant_id FK (nullable) a: talleres, mecanicos, administradores,
  asignaciones_servicio, servicios_realizados, comisiones
- Crear índices en cada tenant_id para performance
"""

from alembic import op
import sqlalchemy as sa


revision = 'c5d6e7f8a9b0'
down_revision = 'b3c4d5e6f7a8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ===========================================================
    # PASO 1: Crear la tabla tenants (el ENUM se crea automáticamente)
    # ===========================================================
    op.create_table(
        "tenants",
        sa.Column("id",             sa.Integer(),    nullable=False),
        sa.Column("nombre",         sa.String(200),  nullable=False),
        sa.Column("plan",           sa.Enum("basico", "profesional", "enterprise", name="plan_tenant"), nullable=False),
        sa.Column("activo",         sa.Boolean(),    nullable=False, server_default="true"),
        sa.Column("fecha_registro", sa.DateTime(),   nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre"),
    )
    op.create_index("ix_tenants_id", "tenants", ["id"])

    # ===========================================================
    # PASO 2: Agregar tenant_id a cada tabla afectada
    # ===========================================================

    # talleres
    op.add_column("talleres", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_talleres_tenant", "talleres", "tenants", ["tenant_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index("ix_talleres_tenant_id", "talleres", ["tenant_id"])

    # mecanicos
    op.add_column("mecanicos", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_mecanicos_tenant", "mecanicos", "tenants", ["tenant_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index("ix_mecanicos_tenant_id", "mecanicos", ["tenant_id"])

    # administradores
    op.add_column("administradores", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_administradores_tenant", "administradores", "tenants", ["tenant_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index("ix_administradores_tenant_id", "administradores", ["tenant_id"])

    # asignaciones_servicio
    op.add_column("asignaciones_servicio", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_asignaciones_tenant", "asignaciones_servicio", "tenants", ["tenant_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index("ix_asignaciones_tenant_id", "asignaciones_servicio", ["tenant_id"])

    # servicios_realizados
    op.add_column("servicios_realizados", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_servicios_tenant", "servicios_realizados", "tenants", ["tenant_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index("ix_servicios_tenant_id", "servicios_realizados", ["tenant_id"])

    # comisiones
    op.add_column("comisiones", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_comisiones_tenant", "comisiones", "tenants", ["tenant_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index("ix_comisiones_tenant_id", "comisiones", ["tenant_id"])



def downgrade() -> None:
    # Revertir en orden inverso

    # comisiones
    op.drop_index("ix_comisiones_tenant_id",   table_name="comisiones")
    op.drop_constraint("fk_comisiones_tenant", "comisiones",           type_="foreignkey")
    op.drop_column("comisiones", "tenant_id")

    # servicios_realizados
    op.drop_index("ix_servicios_tenant_id",    table_name="servicios_realizados")
    op.drop_constraint("fk_servicios_tenant",  "servicios_realizados", type_="foreignkey")
    op.drop_column("servicios_realizados", "tenant_id")

    # asignaciones_servicio
    op.drop_index("ix_asignaciones_tenant_id",  table_name="asignaciones_servicio")
    op.drop_constraint("fk_asignaciones_tenant","asignaciones_servicio", type_="foreignkey")
    op.drop_column("asignaciones_servicio", "tenant_id")

    # administradores
    op.drop_index("ix_administradores_tenant_id", table_name="administradores")
    op.drop_constraint("fk_administradores_tenant","administradores",   type_="foreignkey")
    op.drop_column("administradores", "tenant_id")

    # mecanicos
    op.drop_index("ix_mecanicos_tenant_id",    table_name="mecanicos")
    op.drop_constraint("fk_mecanicos_tenant",  "mecanicos",            type_="foreignkey")
    op.drop_column("mecanicos", "tenant_id")

    # talleres
    op.drop_index("ix_talleres_tenant_id",     table_name="talleres")
    op.drop_constraint("fk_talleres_tenant",   "talleres",             type_="foreignkey")
    op.drop_column("talleres", "tenant_id")

    # tabla tenants
    op.drop_index("ix_tenants_id", table_name="tenants")
    op.drop_table("tenants")
    op.execute("DROP TYPE IF EXISTS plan_tenant")
    op.execute("DROP TYPE IF EXISTS plan_tenant")
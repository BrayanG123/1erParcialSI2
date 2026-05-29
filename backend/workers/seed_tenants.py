"""
Seed script: inserta tenants de prueba y asigna datos existentes.

Ejecución:
    cd backend
    python workers/seed_tenants.py

Seguro de ejecutar múltiples veces (idempotente).
"""

import sys
import os

# Para que Python encuentre los módulos de la app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.tenant import Tenant, PlanTenant
from app.models.taller import Taller
from app.models.usuario import Mecanico, Administrador


def crear_tenant_si_no_existe(db: Session, nombre: str, plan: PlanTenant) -> Tenant:
    """Busca el tenant por nombre; lo crea solo si no existe."""
    tenant = db.query(Tenant).filter(Tenant.nombre == nombre).first()
    if not tenant:
        tenant = Tenant(nombre=nombre, plan=plan, activo=True)
        db.add(tenant)
        db.flush()  # flush para obtener el ID sin hacer commit todavía
        print(f"  [+] Tenant creado: '{nombre}' (plan: {plan.value}, id: {tenant.id})")
    else:
        print(f"  [=] Tenant ya existe: '{nombre}' (id: {tenant.id})")
    return tenant


def asignar_tenant_a_taller(db: Session, taller: Taller, tenant: Tenant) -> None:
    """Asigna el tenant al taller, a su admin y a sus mecánicos."""
    taller.tenant_id = tenant.id

    if taller.administrador:
        taller.administrador.tenant_id = tenant.id

    for mecanico in taller.mecanicos:
        mecanico.tenant_id = tenant.id

    mecánicos_count = len(taller.mecanicos)
    print(f"    -> Taller '{taller.nombre}' → tenant '{tenant.nombre}' "
          f"({mecánicos_count} mecánico(s) asignado(s))")
    

def seed(db: Session) -> None:
    print("\n=== SEEDING TENANTS ===\n")

    # ----------------------------------------------------------
    # PASO 1: Crear los tenants de prueba
    # ----------------------------------------------------------
    print("1. Creando tenants...")
    tenant_norte = crear_tenant_si_no_existe(
        db, nombre="Auxilio Norte", plan=PlanTenant.profesional
    )
    tenant_express = crear_tenant_si_no_existe(
        db, nombre="Mecánicos Express", plan=PlanTenant.basico
    )
    db.flush()

    # ----------------------------------------------------------
    # PASO 2: Cargar todos los talleres existentes
    # ----------------------------------------------------------
    talleres = db.query(Taller).all()
    print(f"\n2. Talleres encontrados en BD: {len(talleres)}")

    if not talleres:
        print("   No hay talleres. Crea talleres primero con POST /auth/setup-taller")
        print("   El script finalizó sin asignar talleres.")
        db.commit()
        return

    # ----------------------------------------------------------
    # PASO 3: Distribuir talleres entre los dos tenants
    #         Los pares van a "Auxilio Norte", los impares a "Mecánicos Express"
    #         Si ya tienen tenant asignado, se respeta.
    # ----------------------------------------------------------
    print("\n3. Asignando talleres a tenants...")
    sin_tenant = [t for t in talleres if t.tenant_id is None]
    con_tenant = [t for t in talleres if t.tenant_id is not None]

    print(f"   Talleres ya asignados: {len(con_tenant)}")
    print(f"   Talleres sin asignar:  {len(sin_tenant)}")

    for i, taller in enumerate(sin_tenant):
        # Alternar entre los dos tenants
        tenant_destino = tenant_norte if i % 2 == 0 else tenant_express
        asignar_tenant_a_taller(db, taller, tenant_destino)

    # ----------------------------------------------------------
    # PASO 4: Asignar mecánicos y admins que quedaron sin tenant
    #         (posible si existen sin taller asignado)
    # ----------------------------------------------------------
    print("\n4. Verificando mecánicos sin tenant...")
    mecanicos_sin_tenant = db.query(Mecanico).filter(Mecanico.tenant_id.is_(None)).all()
    print(f"   Mecánicos sin tenant: {len(mecanicos_sin_tenant)}")
    for m in mecanicos_sin_tenant:
        m.tenant_id = tenant_norte.id
        print(f"   -> Mecánico id={m.id} → tenant '{tenant_norte.nombre}'")

    print("\n5. Verificando administradores sin tenant...")
    admins_sin_tenant = db.query(Administrador).filter(Administrador.tenant_id.is_(None)).all()
    print(f"   Admins sin tenant: {len(admins_sin_tenant)}")
    for a in admins_sin_tenant:
        a.tenant_id = tenant_norte.id
        print(f"   -> Admin id={a.id} → tenant '{tenant_norte.nombre}'")

    # ----------------------------------------------------------
    # PASO 5: Confirmar todo
    # ----------------------------------------------------------
    db.commit()
    print("\n=== SEEDING COMPLETADO ===")
    print(f"  Tenant 1: '{tenant_norte.nombre}' (id: {tenant_norte.id})")
    print(f"  Tenant 2: '{tenant_express.nombre}' (id: {tenant_express.id})")
    print("\nPróximo paso: haz login con un administrador y verifica que")
    print("el token JWT incluye 'tenant_id' con un valor numérico.")


if __name__ == "__main__":
    db: Session = SessionLocal()
    try:
        seed(db)
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] El seeding falló: {e}")
        raise
    finally:
        db.close()
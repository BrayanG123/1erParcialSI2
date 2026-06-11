# Cambios en los Seeders — Relación Tenant ↔ Taller 1 a 1

**Fecha:** 2026-06-10
**Motivo:** El seed generaba 2 tenants con 10 talleres cada uno, pero el diseño correcto
(y el flujo real de producción) es **un tenant por cada taller** (relación 1 a 1).

---

## 1. El problema

El script `backend/workers/seed_data.py` original hacía esto:

```
crear_tenants()            → creaba 2 tenants fijos: "Auxilio Norte" y "Mecánicos Express"
crear_talleres_y_personal() → creaba 10 talleres POR CADA tenant (20 en total)
```

Resultado: 2 tenants, 20 talleres → cada tenant "agrupaba" 10 talleres.

Esto contradecía el flujo de producción: cuando un administrador registra su taller
(`backend/app/crud/taller.py` → `crear_taller()`), se crea **un Tenant nuevo exclusivo
para ese taller**, con el mismo nombre. Es decir, producción siempre fue 1:1.

## 2. ¿Los modelos permiten la relación 1 a 1?

**Sí, sin ningún cambio.** En `backend/app/models/taller.py`:

```python
tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True)
tenant = relationship("Tenant", back_populates="talleres")
```

La FK es simple: nada obliga a que un tenant tenga varios talleres. La relación 1:N
de SQLAlchemy admite el caso 1:1 como un caso particular (la lista `tenant.talleres`
simplemente tendrá un solo elemento). **No se tocaron los modelos ni hubo migración.**

## 3. Qué se cambió en `backend/workers/seed_data.py`

### a) Se eliminó la función `crear_tenants()`
Ya no existen los tenants fijos "Auxilio Norte" y "Mecánicos Express".

### b) `crear_talleres_y_personal()` ahora crea el tenant junto al taller

```python
NUM_TALLERES = 20

for idx in range(1, NUM_TALLERES + 1):
    nombre_taller = f"{nombre_base} T{idx}"          # ej: "Taller Norte T1"

    # Tenant 1:1 — MISMO nombre que el taller (igual que producción)
    tenant = Tenant(
        nombre=nombre_taller,
        plan=random.choice([basico, profesional, enterprise]),  # variedad para KPIs
        activo=True,
    )
    db.add(tenant)
    db.flush()                  # asigna el id del tenant antes de usarlo

    taller = Taller(..., tenant_id=tenant.id)        # ← vínculo 1:1
```

Los 2 admins y 5 mecánicos de cada taller reciben el `tenant_id` de SU taller
(antes recibían el tenant compartido).

### c) Limpieza de la firma de `crear_incidentes_historicos()`
Se quitó el parámetro `tenants` porque **nunca se usaba**: el `tenant_id` de cada
asignación/servicio/comisión siempre se obtuvo del mecánico elegido
(`mecanicos[0].tenant_id`), así que los incidentes históricos quedan correctamente
repartidos entre los 20 tenants sin cambios adicionales.

### d) Renumeración de pasos
Al fusionar tenants+talleres en un paso, el flujo pasó de `[1/5]..[5/5]` a `[1/4]..[4/4]`:

```
[1/4] Categorías
[2/4] Tenants y talleres (1 tenant por taller)
[3/4] Clientes y vehículos
[4/4] Incidentes históricos
```

## 4. Resultado esperado tras el seed

| Tabla | Antes | Ahora |
|-------|-------|-------|
| tenants | 2 | **20** (uno por taller, mismo nombre) |
| talleres | 20 | 20 |
| admins | 40 | 40 |
| mecánicos | 100 | 100 |
| (resto) | igual | igual |

## 5. Lecciones actualizadas

- **`modulos_y_lecciones/modulo-3-seeding/leccion-3-1-seed-masivo.md`**
  El bloque de código es espejo del script real. Se actualizó el objetivo, el docstring,
  la salida esperada y se marcó `seed_tenants.py` (lección 1.3) como obsoleto.

- **`modulos_y_lecciones/modulo-3-seeding/leccion-3-2-validacion-datos.md`**
  - Conteo esperado de tenants: 2 → 20.
  - **Dos validaciones nuevas** para garantizar la relación 1 a 1 (deben dar 0):

    ```sql
    -- Talleres sin tenant
    SELECT COUNT(*) FROM talleres WHERE tenant_id IS NULL;

    -- Tenants con más de un taller (violaría el 1 a 1)
    SELECT COUNT(*) FROM (
        SELECT tenant_id FROM talleres
        WHERE tenant_id IS NOT NULL
        GROUP BY tenant_id HAVING COUNT(*) > 1
    ) sub;
    ```
  - Se actualizó el SQL de limpieza (sección 7) para borrar los tenants del seed
    por su patrón de nombre (`' T<número>'` al final) y los 2 tenants legacy.

## 6. ⚠️ IMPORTANTE — Cómo regenerar tu base de datos

Los talleres nuevos usan **los mismos nombres** que los viejos ("Taller Norte T1", etc.).
Como el seed es idempotente (verifica por nombre), si tu BD ya tiene el seed anterior
**el script va a saltar todo y quedará la estructura vieja de 2 tenants**.

Pasos para regenerar:

```sql
-- 1. En psql: ejecutar el SQL de limpieza de la sección 7 de la lección 3.2
TRUNCATE TABLE calificaciones, pagos, comisiones, servicios_realizados,
    historial_estados, asignaciones_servicio, incidentes, vehiculos
    RESTART IDENTITY CASCADE;

DELETE FROM mecanicos WHERE usuario_id IN (SELECT id FROM usuarios WHERE username LIKE 'mec_t%');
DELETE FROM administradores WHERE usuario_id IN (SELECT id FROM usuarios WHERE username LIKE 'adm_t%');
DELETE FROM clientes WHERE usuario_id IN (SELECT id FROM usuarios WHERE username LIKE 'cli_%');
DELETE FROM usuarios WHERE username LIKE 'cli_%' OR username LIKE 'mec_t%' OR username LIKE 'adm_t%';

DELETE FROM talleres WHERE nombre ~ ' T[0-9]+$';
DELETE FROM tenants  WHERE nombre ~ ' T[0-9]+$';
DELETE FROM tenants  WHERE nombre IN ('Auxilio Norte', 'Mecánicos Express');
```

```bash
# 2. Re-ejecutar el seed
cd backend
python workers/seed_data.py

# 3. Validar (los checks de 1:1 deben dar 0)
#    (el script validate_seed.py está en la lección 3.2, créalo si aún no existe)
```

> Nota: la limpieza NO toca a los usuarios/talleres que creaste manualmente
> (solo borra los que siguen los patrones del seed: `cli_*`, `adm_t*`, `mec_t*`
> y nombres terminados en ` T<número>`).

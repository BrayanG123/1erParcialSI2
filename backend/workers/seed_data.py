"""
seed_data.py — Seeding masivo para el sistema de auxilio vehicular.

Genera:
  - 2 tenants
  - 20 talleres (10 por tenant), 40 admins (2 por taller), 100 mecánicos (5 por taller)
  - 500 clientes con 1-2 vehículos cada uno
  - 2000 incidentes históricos (últimos 6 meses)
    - 65% completados (flujo completo: asignacion → servicio → pago → comision → calificacion)
    - 20% cancelados
    - 15% disponibles (sin asignación)

Ejecución:
    cd backend
    python workers/seed_data.py
"""


import sys
import os
import random
from datetime import datetime, timedelta

# Agregar la carpeta backend/ al path de Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.core.security import hash_password
from app.models.tenant import Tenant, PlanTenant
from app.models.taller import Taller
from app.models.usuario import Usuario, RolUsuario, Cliente, Mecanico, Administrador
from app.models.vehiculo import Vehiculo
from app.models.categoria import Categoria
from app.models.incidente import Incidente, EstadoIncidente
from app.models.asignacion_servicio import AsignacionServicio, EstadoAsignacion
from app.models.historial_estado import HistorialEstado
from app.models.servicio_realizado import ServicioRealizado
from app.models.pago import Pago, EstadoPago, MetodoPago
from app.models.comision import Comision
from app.models.calificacion import Calificacion



# ─────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────

# Coordenadas centrales — Cochabamba, Bolivia
LAT_CENTRO = -17.3895
LNG_CENTRO = -66.1540

# Contraseña única para todos los usuarios del seed (más rápido hashear una sola vez)
PASSWORD_HASH = hash_password("Test1234")


TALLERES_NOMBRES = [
    "Taller Norte", 
    "Servicio Automotriz Central", 
    "Mecánica Express",
    "Auto Servicio Rápido", 
    "Taller del Valle", 
    "Mecánica Moderna",
    "Servicio Técnico VIP", 
    "Taller San Martín", 
    "AutoFix Pro", 
    "Mecánica 24hrs",
]


ESPECIALIDADES_MECANICO = [
    "Motor y transmisión", 
    "Sistema eléctrico", 
    "Frenos y dirección",
    "Llantas y suspensión", 
    "Chapería y pintura", 
    "Aire acondicionado",
    "Diagnóstico general", 
    "Auxilio en ruta",
]

MODELOS_VEHICULO = [
    "Corolla", "Civic", "Yaris", "Sandero", "Logan", "Hilux",
    "Fortuner", "RAV4", "CRV", "Tucson", "Sportage", "Accent",
    "Aveo", "Spark", "Fiesta", "Focus", "Golf", "Polo", "Tiguan",
]

COLORES_VEHICULO = [
    "Blanco", "Negro", "Gris", "Rojo", "Azul", "Plata",
    "Verde", "Beige", "Marrón", "Naranja",
]

CATEGORIAS_DATA = [
    {"nombre": "Batería descargada", "descripcion": "El vehículo no enciende por batería agotada", "prioridad": 1},
    {"nombre": "Llanta pinchada",    "descripcion": "Neumático desinflado o reventado",           "prioridad": 1},
    {"nombre": "Motor recalentado",  "descripcion": "Temperatura del motor por encima del límite", "prioridad": 2},
    {"nombre": "Choque leve",        "descripcion": "Colisión menor sin heridos",                  "prioridad": 2},
    {"nombre": "Fallo eléctrico",    "descripcion": "Problemas con el sistema eléctrico",          "prioridad": 2},
    {"nombre": "Accidente",          "descripcion": "Colisión con daños significativos",           "prioridad": 3},
    {"nombre": "Sin combustible",    "descripcion": "Vehículo sin gasolina o diésel",              "prioridad": 1},
    {"nombre": "Fallo de frenos",    "descripcion": "Sistema de frenos no responde correctamente", "prioridad": 3},
]

DESCRIPCIONES_POR_CATEGORIA = {
    "Batería descargada": [
        "El auto no enciende, la batería está completamente descargada",
        "Intenté arrancar y solo escucho un clic, batería muerta",
        "Las luces no encienden, creo que se descargó la batería",
    ],
    "Llanta pinchada": [
        "Llanta trasera derecha completamente desinflada",
        "Reventé una llanta en la autopista, necesito auxilio",
        "La llanta delantera izquierda perdió presión repentinamente",
    ],
    "Motor recalentado": [
        "El indicador de temperatura está en rojo y salió humo del capó",
        "El motor se calentó demasiado, lo apagué en la vía",
        "El agua del radiador se terminó, motor sobrecalentado",
    ],
    "Choque leve": [
        "Choque leve en estacionamiento, el parachoques está dañado",
        "Golpeé un poste a baja velocidad, necesito asistencia",
        "Choqué con otro vehículo, solo daños leves en la carrocería",
    ],
    "Fallo eléctrico": [
        "El tablero no enciende, todos los sistemas eléctricos fallaron",
        "El auto se apagó solo mientras manejaba, no responde",
        "Cortocircuito en el sistema eléctrico, veo chispas",
    ],
    "Accidente": [
        "Accidente en la avenida principal, vehículo inmovilizado",
        "Colisión fuerte, necesito grúa y asistencia inmediata",
        "Choque con camión, el auto no puede moverse",
    ],
    "Sin combustible": [
        "Se me acabó la gasolina en la ruta",
        "El tanque está vacío, necesito que traigan combustible",
        "Me quedé sin diésel en la carretera",
    ],
    "Fallo de frenos": [
        "Los frenos no responden bien, siento que se van al fondo",
        "Fallo del sistema de frenos, el auto no para correctamente",
        "Escucho un ruido metálico al frenar y el auto no para bien",
    ],
}


TIPOS_SERVICIO_POR_CATEGORIA = {
    "Batería descargada": "Carga o reemplazo de batería",
    "Llanta pinchada":    "Cambio de llanta",
    "Motor recalentado":  "Servicio de refrigeración y radiador",
    "Choque leve":        "Reparación de carrocería leve",
    "Fallo eléctrico":    "Diagnóstico y reparación eléctrica",
    "Accidente":          "Evaluación y reparación por accidente",
    "Sin combustible":    "Suministro de combustible de emergencia",
    "Fallo de frenos":    "Reparación del sistema de frenos",
}

COSTOS_POR_CATEGORIA = {
    "Batería descargada": (80,  250),
    "Llanta pinchada":    (50,  150),
    "Motor recalentado":  (200, 600),
    "Choque leve":        (300, 800),
    "Fallo eléctrico":    (150, 500),
    "Accidente":          (500, 2000),
    "Sin combustible":    (40,  100),
    "Fallo de frenos":    (200, 700),
}



# ─────────────────────────────────────────────────────────────
# FUNCIONES DE UTILIDAD
# ─────────────────────────────────────────────────────────────

def coords_aleatorias(radio: float = 0.15) -> tuple[float, float]:
    """Genera coordenadas aleatorias dentro del radio dado desde el centro."""
    lat = LAT_CENTRO + random.uniform(-radio, radio)
    lng = LNG_CENTRO + random.uniform(-radio, radio)
    return round(lat, 6), round(lng, 6)


def fecha_aleatoria(desde_dias: int = 180) -> datetime:
    """Fecha aleatoria dentro de los últimos N días."""
    delta = random.randint(0, desde_dias)
    return datetime.utcnow() - timedelta(days=delta, hours=random.randint(0, 23))


def sumar_minutos(base: datetime, min_min: int, max_min: int) -> datetime:
    """Suma minutos aleatorios a una fecha."""
    return base + timedelta(minutes=random.randint(min_min, max_min))



# ─────────────────────────────────────────────────────────────
# SECCIÓN 1 — CATEGORÍAS
# ─────────────────────────────────────────────────────────────

def crear_categorias(db: Session) -> dict[str, Categoria]:
    """Crea las categorías de incidente si no existen. Retorna dict {nombre: objeto}."""
    print("\n[1/5] Creando categorías...")
    categorias = {}
    for data in CATEGORIAS_DATA:
        cat = db.query(Categoria).filter(Categoria.nombre == data["nombre"]).first()
        if not cat:
            cat = Categoria(**data)
            db.add(cat)
            print(f"  [+] Categoría: {data['nombre']}")
        else:
            print(f"  [=] Categoría ya existe: {data['nombre']}")
        categorias[data["nombre"]] = cat
    db.flush()
    return categorias



# ─────────────────────────────────────────────────────────────
# SECCIÓN 2 — TENANTS
# ─────────────────────────────────────────────────────────────

def crear_tenants(db: Session) -> list[Tenant]:
    """Crea 2 tenants de prueba si no existen."""
    print("\n[2/5] Creando tenants...")
    tenants_data = [
        {"nombre": "Auxilio Norte",     "plan": PlanTenant.profesional},
        {"nombre": "Mecánicos Express", "plan": PlanTenant.basico},
    ]
    tenants = []
    for data in tenants_data:
        t = db.query(Tenant).filter(Tenant.nombre == data["nombre"]).first()
        if not t:
            t = Tenant(nombre=data["nombre"], plan=data["plan"], activo=True)
            db.add(t)
            db.flush()
            print(f"  [+] Tenant: {t.nombre} (id={t.id})")
        else:
            print(f"  [=] Tenant ya existe: {t.nombre} (id={t.id})")
        tenants.append(t)
    return tenants



# ─────────────────────────────────────────────────────────────
# SECCIÓN 3 — TALLERES, ADMINS Y MECÁNICOS
# ─────────────────────────────────────────────────────────────

def crear_talleres_y_personal(
    db: Session, tenants: list[Tenant]
) -> dict[int, list[Mecanico]]:
    """
    Crea 10 talleres por tenant (20 total), 2 admins y 5 mecánicos por taller.
    Retorna dict {taller_id: [lista de mecánicos]}.
    """
    print("\n[3/5] Creando talleres, admins y mecánicos...")
    mecanicos_por_taller: dict[int, list[Mecanico]] = {}

    taller_global_idx = 0  # índice único para nombres y usernames

    for tenant in tenants:
        print(f"  Tenant: {tenant.nombre}")

        for i in range(10):
            taller_global_idx += 1
            nombre_taller = f"{TALLERES_NOMBRES[i]} T{taller_global_idx}"

            # Verificar si ya existe
            taller_existente = (
                db.query(Taller).filter(Taller.nombre == nombre_taller).first()
            )
            if taller_existente:
                print(f"    [=] Taller ya existe: {nombre_taller}")
                mecanicos_existentes = (
                    db.query(Mecanico)
                    .filter(Mecanico.taller_id == taller_existente.id)
                    .all()
                )
                mecanicos_por_taller[taller_existente.id] = mecanicos_existentes
                continue

            lat, lng = coords_aleatorias(radio=0.12)
            taller = Taller(
                nombre=nombre_taller,
                direccion=f"Calle Seed {taller_global_idx}, Zona {i+1}",
                telefono=f"7{random.randint(1000000, 9999999)}",
                latitud=lat,
                longitud=lng,
                calificacion_promedio=round(random.uniform(3.5, 5.0), 1),
                is_active=True,
                tenant_id=tenant.id,
            )
            db.add(taller)
            db.flush()

            # Crear 2 administradores por taller
            for a in range(2):
                username_admin = f"adm_t{taller_global_idx}_a{a}"
                email_admin    = f"adm{taller_global_idx}{a}@seed.com"

                u_admin = Usuario(
                    nombre=f"Admin{taller_global_idx}",
                    apellido=f"Taller{a}",
                    email=email_admin,
                    username=username_admin,
                    password_hash=PASSWORD_HASH,
                    rol=RolUsuario.administrador,
                )
                db.add(u_admin)
                db.flush()

                perfil_admin = Administrador(
                    usuario_id=u_admin.id,
                    taller_id=taller.id,
                    tenant_id=tenant.id,
                )
                db.add(perfil_admin)

            # Crear 5 mecánicos por taller
            mecanicos_del_taller = []
            for m in range(5):
                username_mec = f"mec_t{taller_global_idx}_m{m}"
                email_mec    = f"mec{taller_global_idx}{m}@seed.com"
                lat_m, lng_m = coords_aleatorias(radio=0.05)

                u_mec = Usuario(
                    nombre=f"Mecánico{taller_global_idx}",
                    apellido=f"Num{m}",
                    email=email_mec,
                    username=username_mec,
                    password_hash=PASSWORD_HASH,
                    rol=RolUsuario.mecanico,
                )
                db.add(u_mec)
                db.flush()

                perfil_mec = Mecanico(
                    usuario_id=u_mec.id,
                    taller_id=taller.id,
                    tenant_id=tenant.id,
                    especialidad=random.choice(ESPECIALIDADES_MECANICO),
                    estado="disponible",
                    latitud=lat_m,
                    longitud=lng_m,
                )
                db.add(perfil_mec)
                db.flush()
                mecanicos_del_taller.append(perfil_mec)

            mecanicos_por_taller[taller.id] = mecanicos_del_taller
            print(f"    [+] Taller #{taller.id}: {nombre_taller} (5 mec, 2 adm)")

        db.commit()

    return mecanicos_por_taller



# ─────────────────────────────────────────────────────────────
# SECCIÓN 4 — CLIENTES Y VEHÍCULOS
# ─────────────────────────────────────────────────────────────

def crear_clientes_y_vehiculos(
    db: Session, total_clientes: int = 500
) -> list[tuple[Cliente, list[Vehiculo]]]:
    """
    Crea N clientes con 1-2 vehículos cada uno.
    Retorna lista de tuplas (cliente, [vehiculos]).
    """
    print(f"\n[4/5] Creando {total_clientes} clientes con vehículos...")

    # Verificar cuántos clientes ya existen del seed
    ya_existen = (
        db.query(Usuario)
        .filter(Usuario.username.like("cli_%"))
        .count()
    )
    if ya_existen >= total_clientes:
        print(f"  [=] Ya existen {ya_existen} clientes del seed. Cargando...")
        clientes_db = (
            db.query(Cliente)
            .join(Usuario, Cliente.usuario_id == Usuario.id)
            .filter(Usuario.username.like("cli_%"))
            .limit(total_clientes)
            .all()
        )
        resultado = []
        for c in clientes_db:
            resultado.append((c, c.vehiculos))
        return resultado

    resultado = []
    placas_usadas: set[str] = set(
        row[0] for row in db.query(Vehiculo.placa).all()
    )

    BATCH_SIZE = 50
    for i in range(total_clientes):
        username = f"cli_{i:04d}"

        # Saltar si ya existe
        if db.query(Usuario).filter(Usuario.username == username).first():
            u = db.query(Usuario).filter(Usuario.username == username).first()
            c = u.perfil_cliente
            resultado.append((c, c.vehiculos))
            continue

        u = Usuario(
            nombre=f"Cliente{i:04d}",
            apellido=f"Apellido{random.randint(1, 200)}",
            email=f"cli{i:04d}@seed.com",
            username=username,
            password_hash=PASSWORD_HASH,
            rol=RolUsuario.cliente,
        )
        db.add(u)
        db.flush()

        perfil_cliente = Cliente(usuario_id=u.id)
        db.add(perfil_cliente)
        db.flush()

        # Crear 1-2 vehículos
        vehiculos_del_cliente = []
        num_vehiculos = random.choices([1, 2], weights=[70, 30])[0]
        for v in range(num_vehiculos):
            # Generar placa única
            while True:
                placa = f"SBD{i:04d}{v}"
                if placa not in placas_usadas:
                    placas_usadas.add(placa)
                    break
                placa = f"CBB{i:04d}{random.randint(0, 9)}"

            vehiculo = Vehiculo(
                cliente_id=perfil_cliente.id,
                placa=placa,
                modelo=random.choice(MODELOS_VEHICULO),
                color=random.choice(COLORES_VEHICULO),
            )
            db.add(vehiculo)
            vehiculos_del_cliente.append(vehiculo)

        db.flush()
        resultado.append((perfil_cliente, vehiculos_del_cliente))

        if (i + 1) % BATCH_SIZE == 0:
            db.commit()
            print(f"  ... {i + 1}/{total_clientes} clientes creados")

    db.commit()
    print(f"  [✓] {total_clientes} clientes con sus vehículos creados")
    return resultado



# ─────────────────────────────────────────────────────────────
# SECCIÓN 5 — INCIDENTES HISTÓRICOS
# ─────────────────────────────────────────────────────────────

def crear_incidentes_historicos(
    db: Session,
    clientes_vehiculos: list[tuple[Cliente, list[Vehiculo]]],
    mecanicos_por_taller: dict[int, list[Mecanico]],
    categorias: dict[str, Categoria],
    tenants: list[Tenant],
    total_incidentes: int = 2000,
) -> None:
    """
    Genera N incidentes históricos distribuidos en los últimos 6 meses.

    Distribución:
      65% completados → flujo completo (asignación, servicio, pago, comisión, calificación)
      20% cancelados  → asignación en estado cancelado
      15% disponibles → solo el incidente, sin asignación
    """
    print(f"\n[5/5] Creando {total_incidentes} incidentes históricos...")

    # Verificar cuántos ya existen
    ya_existen = db.query(Incidente).count()
    if ya_existen >= total_incidentes:
        print(f"  [=] Ya existen {ya_existen} incidentes. Saltando.")
        return

    # Construir lista plana de (taller_id, [mecanicos], tenant_id)
    recursos_talleres = []
    for taller_id, mecanicos in mecanicos_por_taller.items():
        if not mecanicos:
            continue
        # Obtener tenant del primer mecánico del taller
        tenant_id = mecanicos[0].tenant_id
        recursos_talleres.append({
            "taller_id": taller_id,
            "mecanicos": mecanicos,
            "tenant_id": tenant_id,
        })

    if not recursos_talleres:
        print("  [!] No hay talleres con mecánicos. Ejecuta el seed de talleres primero.")
        return

    nombres_categorias = list(categorias.keys())
    BATCH_SIZE = 100
    completados = 0
    cancelados  = 0
    disponibles = 0

    for idx in range(total_incidentes):
        # Elegir cliente y vehículo aleatorio
        cliente, vehiculos = random.choice(clientes_vehiculos)
        vehiculo = random.choice(vehiculos) if vehiculos else None

        # Elegir categoría
        nombre_cat = random.choice(nombres_categorias)
        categoria  = categorias[nombre_cat]

        # Coordenadas aleatorias del incidente
        lat, lng = coords_aleatorias(radio=0.18)

        # Fecha de creación aleatoria en los últimos 180 días
        fecha_creacion = fecha_aleatoria(desde_dias=180)

        incidente = Incidente(
            cliente_id=cliente.id,
            vehiculo_id=vehiculo.id if vehiculo else None,
            categoria_id=categoria.id,
            descripcion=random.choice(DESCRIPCIONES_POR_CATEGORIA[nombre_cat]),
            latitud=lat,
            longitud=lng,
            fecha_hora=fecha_creacion,
            estado=EstadoIncidente.no_disponible,  # la mayoría están atendidos
        )
        db.add(incidente)
        db.flush()

        # Elegir taller y mecánico aleatorio
        recurso = random.choice(recursos_talleres)
        mecanico = random.choice(recurso["mecanicos"])
        tenant_id = recurso["tenant_id"]

        # ── Decidir el destino del incidente ──────────────────
        dado = random.random()

        if dado < 0.65:
            # ── FLUJO COMPLETO ─────────────────────────────────
            _crear_flujo_completo(
                db, incidente, mecanico, tenant_id, nombre_cat, fecha_creacion
            )
            completados += 1

        elif dado < 0.85:
            # ── CANCELADO ──────────────────────────────────────
            _crear_asignacion_cancelada(
                db, incidente, mecanico, tenant_id, fecha_creacion
            )
            cancelados += 1

        else:
            # ── DISPONIBLE (sin atender) ───────────────────────
            incidente.estado = EstadoIncidente.disponible
            disponibles += 1

        if (idx + 1) % BATCH_SIZE == 0:
            db.commit()
            print(f"  ... {idx + 1}/{total_incidentes} incidentes | "
                  f"completados={completados} cancelados={cancelados} "
                  f"disponibles={disponibles}")

    db.commit()
    print(f"\n  [✓] Incidentes generados: {total_incidentes}")
    print(f"      Completados:  {completados}")
    print(f"      Cancelados:   {cancelados}")
    print(f"      Disponibles:  {disponibles}")



def _crear_flujo_completo(
    db: Session,
    incidente: Incidente,
    mecanico: Mecanico,
    tenant_id: int | None,
    nombre_categoria: str,
    fecha_base: datetime,
) -> None:
    """Crea el flujo completo para un incidente: asignación → servicio → pago → comisión → calificación."""

    # ── Asignación ────────────────────────────────────────────
    fecha_asignacion = sumar_minutos(fecha_base, 5, 30)
    distancia = round(random.uniform(0.5, 15.0), 2)
    costo_min, costo_max = COSTOS_POR_CATEGORIA.get(nombre_categoria, (100, 500))
    costo_estimado = round(random.uniform(costo_min * 0.8, costo_max * 0.9), 2)

    asignacion = AsignacionServicio(
        incidente_id=incidente.id,
        mecanico_id=mecanico.id,
        tenant_id=tenant_id,
        costo_estimado=costo_estimado,
        distancia_km=distancia,
        tiempo_estimado=int(distancia * 4 + random.randint(5, 20)),
        estado=EstadoAsignacion.finalizado,
        fecha_creacion=fecha_asignacion,
        fecha_respuesta=sumar_minutos(fecha_asignacion, 2, 10),
    )
    db.add(asignacion)
    db.flush()

    # ── Historial de estados ───────────────────────────────────
    fecha_taller   = sumar_minutos(fecha_asignacion, 2, 10)
    fecha_camino   = sumar_minutos(fecha_taller, 5, 20)
    fecha_atencion = sumar_minutos(fecha_camino, int(distancia * 3) + 5, int(distancia * 4) + 30)
    fecha_fin      = sumar_minutos(fecha_atencion, 20, 120)

    historial_entries = [
        HistorialEstado(
            asignacion_id=asignacion.id,
            estado_anterior=EstadoAsignacion.pendiente.value,
            estado_actual=EstadoAsignacion.taller_asignado.value,
            fecha_cambio=fecha_taller,
        ),
        HistorialEstado(
            asignacion_id=asignacion.id,
            estado_anterior=EstadoAsignacion.taller_asignado.value,
            estado_actual=EstadoAsignacion.en_camino.value,
            fecha_cambio=fecha_camino,
        ),
        HistorialEstado(
            asignacion_id=asignacion.id,
            estado_anterior=EstadoAsignacion.en_camino.value,
            estado_actual=EstadoAsignacion.en_atencion.value,
            fecha_cambio=fecha_atencion,
        ),
        HistorialEstado(
            asignacion_id=asignacion.id,
            estado_anterior=EstadoAsignacion.en_atencion.value,
            estado_actual=EstadoAsignacion.finalizado.value,
            fecha_cambio=fecha_fin,
        ),
    ]
    db.add_all(historial_entries)

    # ── Servicio realizado ─────────────────────────────────────
    costo_final = round(random.uniform(costo_min, costo_max), 2)
    servicio = ServicioRealizado(
        asignacion_id=asignacion.id,
        tenant_id=tenant_id,
        tipo_servicio=TIPOS_SERVICIO_POR_CATEGORIA.get(nombre_categoria, "Servicio general"),
        descripcion_trabajo=f"Trabajo realizado: {nombre_categoria.lower()}. "
                            f"Mecánico atendió en {int(distancia * 4)} minutos.",
        costo_final=costo_final,
        observaciones="Servicio completado sin incidencias." if random.random() > 0.3 else None,
        fecha_realizado=fecha_fin,
    )
    db.add(servicio)
    db.flush()

    # ── Pago ─────────────────────────────────────────────────
    metodo = random.choices(
        [MetodoPago.efectivo, MetodoPago.pasarela],
        weights=[70, 30]
    )[0]
    pago = Pago(
        servicio_id=servicio.id,
        monto=costo_final,
        estado=EstadoPago.pagado,
        metodo=metodo,
        referencia=f"REF-{random.randint(100000, 999999)}" if metodo == MetodoPago.pasarela else None,
        fecha_pago=sumar_minutos(fecha_fin, 0, 60),
    )
    db.add(pago)

    # ── Comisión (10% de la plataforma) ───────────────────────
    comision = Comision(
        servicio_id=servicio.id,
        tenant_id=tenant_id,
        porcentaje=10.0,
        monto=round(costo_final * 0.10, 2),
        fecha_emision=fecha_fin,
        fecha_pago=sumar_minutos(fecha_fin, 1440, 4320) if random.random() > 0.3 else None,
    )
    db.add(comision)

    # ── Calificación (80% de los completados tienen calificación) ─
    if random.random() < 0.80:
        puntuacion = random.choices(
            [1, 2, 3, 4, 5],
            weights=[2, 5, 10, 30, 53]  # mayoría 4 y 5 estrellas
        )[0]
        comentarios = [
            "Excelente servicio, muy rápido",
            "Buen servicio, llegaron en el tiempo estimado",
            "Servicio correcto, sin problemas",
            "Llegaron tarde pero resolvieron bien",
            "Malo, el mecánico no supo qué hacer al principio",
            "Muy buen trabajo, lo recomiendo",
            None,
        ]
        calificacion = Calificacion(
            servicio_id=servicio.id,
            puntuacion=puntuacion,
            comentario=random.choice(comentarios),
            fecha=sumar_minutos(fecha_fin, 30, 1440),
        )
        db.add(calificacion)


def _crear_asignacion_cancelada(
    db: Session,
    incidente: Incidente,
    mecanico: Mecanico,
    tenant_id: int | None,
    fecha_base: datetime,
) -> None:
    """Crea una asignación cancelada para el incidente."""
    motivos = [
        "El cliente llamó para cancelar",
        "Mecánico no pudo llegar por tráfico",
        "El cliente resolvió el problema por su cuenta",
        "Error al crear la asignación",
    ]
    fecha_asignacion = sumar_minutos(fecha_base, 5, 30)
    asignacion = AsignacionServicio(
        incidente_id=incidente.id,
        mecanico_id=mecanico.id,
        tenant_id=tenant_id,
        estado=EstadoAsignacion.cancelado,
        fecha_creacion=fecha_asignacion,
        fecha_respuesta=sumar_minutos(fecha_asignacion, 5, 60),
        motivo_rechazo=random.choice(motivos),
    )
    db.add(asignacion)

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def seed(db: Session) -> None:
    print("\n" + "="*55)
    print(" SEED MASIVO — Sistema de Auxilio Vehicular")
    print("="*55)
    print("Contraseña de todos los usuarios del seed: Test1234")

    categorias           = crear_categorias(db)
    tenants              = crear_tenants(db)
    mecanicos_por_taller = crear_talleres_y_personal(db, tenants)
    clientes_vehiculos   = crear_clientes_y_vehiculos(db)
    crear_incidentes_historicos(
        db, clientes_vehiculos, mecanicos_por_taller, categorias, tenants
    )

    print("\n" + "="*55)
    print(" SEED COMPLETADO EXITOSAMENTE")
    print("="*55)
    print("\nCredenciales de ejemplo:")
    print("  Admin taller 1:   adm_t1_a0 / Test1234")
    print("  Mecánico taller 1: mec_t1_m0 / Test1234")
    print("  Cliente 0:        cli_0000  / Test1234")
    print("\nEjecuta la Lección 3.2 para validar la integridad de los datos.")


if __name__ == "__main__":
    db: Session = SessionLocal()
    try:
        seed(db)
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Seed falló: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()
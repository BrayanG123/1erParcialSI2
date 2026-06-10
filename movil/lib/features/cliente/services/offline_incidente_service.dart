// 1. Define IncidentePendiente: el objeto que se guarda en Hive cuando no hay red.
//    Contiene los mismos campos que el formulario de solicitud + metadatos offline.
//
// 2. Define OfflineIncidenteService: CRUD sobre la "caja" de Hive.
//    Métodos: guardar, obtenerTodos, marcarSincronizado, eliminar.

import 'package:hive_flutter/hive_flutter.dart';

// Estructura del Map guardado en Hive:
//   {
//     "idempotencyKey": "550e8400-e29b-41d4-a716-446655440000",
//     "descripcion":    "Llanta pinchada frente al mercado",
//     "latitud":        -17.7834,
//     "longitud":       -63.1812,
//     "clienteId":      42,
//     "vehiculoId":     7,
//     "categoriaId":    3,
//     "rutaFoto":       "/data/user/0/.../foto.jpg",  // path local
//     "rutaAudio":      "/data/user/0/.../audio.m4a", // path local
//     "sincronizado":   false,
//     "timestamp":      "2026-05-31T14:30:00.000Z"
//   }

class IncidentePendiente {

  final String  idempotencyKey; // UUID único generado al guardar
  final String  descripcion;
  final double  latitud;
  final double  longitud;
  final int     clienteId;
  final int?    vehiculoId;
  final int?    categoriaId;
  final String? rutaFoto;       // path absoluto al archivo local
  final String? rutaAudio;      // path absoluto al archivo local
  final bool    sincronizado;   // true = ya fue enviado al backend
  final DateTime timestamp;     // cuándo se creó el registro offline

  const IncidentePendiente({
    required this.idempotencyKey,
    required this.descripcion,
    required this.latitud,
    required this.longitud,
    required this.clienteId,
    this.vehiculoId,
    this.categoriaId,
    this.rutaFoto,
    this.rutaAudio,
    this.sincronizado = false,
    required this.timestamp,
  });

  /// Convierte a Map para guardar en Hive
  Map<String, dynamic> toMap() => {
    'idempotencyKey': idempotencyKey,
    'descripcion':    descripcion,
    'latitud':        latitud,
    'longitud':       longitud,
    'clienteId':      clienteId,
    'vehiculoId':     vehiculoId,
    'categoriaId':    categoriaId,
    'rutaFoto':       rutaFoto,
    'rutaAudio':      rutaAudio,
    'sincronizado':   sincronizado,
    'timestamp':      timestamp.toIso8601String(),
  };

  /// Reconstruye desde el Map guardado en Hive
  factory IncidentePendiente.fromMap(Map<String, dynamic> map) =>
    IncidentePendiente(
      idempotencyKey: map['idempotencyKey'] as String,
      descripcion:    map['descripcion']    as String,
      latitud:        (map['latitud']   as num).toDouble(),
      longitud:       (map['longitud']  as num).toDouble(),
      clienteId:      map['clienteId']  as int,
      vehiculoId:     map['vehiculoId'] as int?,
      categoriaId:    map['categoriaId'] as int?,
      rutaFoto:       map['rutaFoto']   as String?,
      rutaAudio:      map['rutaAudio']  as String?,
      sincronizado:   map['sincronizado'] as bool? ?? false,
      timestamp:      DateTime.parse(map['timestamp'] as String),
    );

  /// Crea una copia marcada como sincronizada
  IncidentePendiente comoSincronizado() => IncidentePendiente(
    idempotencyKey: idempotencyKey,
    descripcion:    descripcion,
    latitud:        latitud,
    longitud:       longitud,
    clienteId:      clienteId,
    vehiculoId:     vehiculoId,
    categoriaId:    categoriaId,
    rutaFoto:       rutaFoto,
    rutaAudio:      rutaAudio,
    sincronizado:   true,       // ← único cambio
    timestamp:      timestamp,
  );

}


// ─── SERVICIO DE ALMACENAMIENTO OFFLINE 
const _kBoxName = 'incidentes_pendientes';

class OfflineIncidenteService {

  static Future<void> init() async {
    await Hive.openBox<Map>(_kBoxName);
  }

  Box<Map> get _box => Hive.box<Map>(_kBoxName);

  /// Guarda un incidente pendiente usando su idempotencyKey como clave primaria.
  Future<void> guardar(IncidentePendiente pendiente) async {
    await _box.put(pendiente.idempotencyKey, pendiente.toMap());
  }

  /// Devuelve todos los incidentes pendientes (sincronizados y no sincronizados).
  List<IncidentePendiente> obtenerTodos() {
    return _box.values
        .map((m) => IncidentePendiente.fromMap(Map<String, dynamic>.from(m)))
        .toList();
  }

  /// Devuelve solo los que aún NO fueron enviados al servidor.
  List<IncidentePendiente> obtenerPendientes() {
    return obtenerTodos().where((p) => !p.sincronizado).toList();
  }

  /// Marca un incidente como enviado exitosamente.
  /// Parámetro: el idempotencyKey del incidente.
  Future<void> marcarSincronizado(String key) async {
    final map = _box.get(key);
    if (map != null) {
      final pendiente = IncidentePendiente.fromMap(Map<String, dynamic>.from(map));
      await _box.put(key, pendiente.comoSincronizado().toMap());
    }
  }

  /// Elimina un incidente de la caja local (para limpieza después de sincronizar).
  Future<void> eliminar(String key) async {
    await _box.delete(key);
  }

  /// Cuántos incidentes están esperando sincronización.
  int get cantidadPendientes => obtenerPendientes().length;

}
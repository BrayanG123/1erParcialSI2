import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';

part 'asignacion_servicio.g.dart';

enum EstadoAsignacion {
  @JsonValue('pendiente')
  pendiente,
  @JsonValue('buscando_taller')
  buscandoTaller,
  @JsonValue('taller_asignado')
  tallerAsignado,      
  @JsonValue('en_camino')
  enCamino,
  @JsonValue('en_atencion')
  enAtencion,          
  @JsonValue('finalizado')
  finalizado,          // ← CORREGIDO: era "completada"
  @JsonValue('cancelado')
  cancelado,           // ← CORREGIDO: era "cancelada"
  @JsonValue('rechazada')
  rechazada,
}

/// Resumen del incidente anidado en la asignación (lo envía el backend
/// para que el mecánico vea descripción, fecha y ubicación del cliente).
@JsonSerializable()
class IncidenteResumen extends Equatable {
  final int id;
  final String descripcion;
  @JsonKey(name: 'fecha_hora')
  final DateTime fechaHora;
  final double? latitud;
  final double? longitud;

  const IncidenteResumen({
    required this.id,
    required this.descripcion,
    required this.fechaHora,
    this.latitud,
    this.longitud,
  });

  factory IncidenteResumen.fromJson(Map<String, dynamic> json) =>
      _$IncidenteResumenFromJson(json);

  Map<String, dynamic> toJson() => _$IncidenteResumenToJson(this);

  @override
  List<Object?> get props => [id, descripcion];
}

@JsonSerializable()
class AsignacionServicio extends Equatable {
  final int id;
  @JsonKey(name: 'costo_estimado')
  final double? costoEstimado;
  @JsonKey(name: 'distancia_km')
  final double? distanciaKm;
  @JsonKey(name: 'tiempo_estimado')
  final int? tiempoEstimado;
  final EstadoAsignacion estado;
  @JsonKey(name: 'fecha_creacion')
  final DateTime fechaCreacion;
  @JsonKey(name: 'fecha_respuesta')
  final DateTime? fechaRespuesta;
  @JsonKey(name: 'motivo_rechazo')
  final String? motivoRechazo;
  @JsonKey(name: 'incidente_id')
  final int incidenteId;
  @JsonKey(name: 'mecanico_id')
  final int? mecanicoId;
  final IncidenteResumen? incidente;

  const AsignacionServicio({
    required this.id,
    this.costoEstimado,
    this.distanciaKm,
    this.tiempoEstimado,
    required this.estado,
    required this.fechaCreacion,
    this.fechaRespuesta,
    this.motivoRechazo,
    required this.incidenteId,
    this.mecanicoId,
    this.incidente,
  });

  factory AsignacionServicio.fromJson(Map<String, dynamic> json) =>
      _$AsignacionServicioFromJson(json);

  Map<String, dynamic> toJson() => _$AsignacionServicioToJson(this);

  @override
  List<Object?> get props => [id, estado, incidenteId, mecanicoId];
}
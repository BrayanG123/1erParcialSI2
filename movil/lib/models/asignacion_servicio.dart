import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';

part 'asignacion_servicio.g.dart';

enum EstadoAsignacion {
  pendiente,
  aceptada,
  rechazada,
  @JsonValue('en_camino')
  enCamino,
  @JsonValue('en_servicio')
  enServicio,
  completada,
  cancelada,
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
  });

  factory AsignacionServicio.fromJson(Map<String, dynamic> json) =>
      _$AsignacionServicioFromJson(json);

  Map<String, dynamic> toJson() => _$AsignacionServicioToJson(this);

  @override
  List<Object?> get props => [id, estado, incidenteId, mecanicoId];
}
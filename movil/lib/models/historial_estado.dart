import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';

part 'historial_estado.g.dart';

@JsonSerializable()
class HistorialEstado extends Equatable {
  final int id;
  @JsonKey(name: 'estado_anterior')
  final String? estadoAnterior;
  @JsonKey(name: 'estado_actual')
  final String estadoActual;
  final String? observacion;
  @JsonKey(name: 'fecha_cambio')
  final DateTime fechaCambio;
  @JsonKey(name: 'asignacion_id')
  final int asignacionId;

  const HistorialEstado({
    required this.id,
    this.estadoAnterior,
    required this.estadoActual,
    this.observacion,
    required this.fechaCambio,
    required this.asignacionId,
  });

  factory HistorialEstado.fromJson(Map<String, dynamic> json) =>
      _$HistorialEstadoFromJson(json);

  Map<String, dynamic> toJson() => _$HistorialEstadoToJson(this);

  @override
  List<Object?> get props => [id, estadoActual, fechaCambio, asignacionId];
}
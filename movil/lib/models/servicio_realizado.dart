import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';

part 'servicio_realizado.g.dart';

@JsonSerializable()
class ServicioRealizado extends Equatable {
  final int id;
  @JsonKey(name: 'tipo_servicio')
  final String tipoServicio;
  @JsonKey(name: 'descripcion_trabajo')
  final String descripcionTrabajo;
  @JsonKey(name: 'costo_final')
  final double costoFinal;
  final String? observaciones;
  @JsonKey(name: 'fecha_realizado')
  final DateTime fechaRealizado;
  @JsonKey(name: 'asignacion_id')
  final int asignacionId;

  const ServicioRealizado({
    required this.id,
    required this.tipoServicio,
    required this.descripcionTrabajo,
    required this.costoFinal,
    this.observaciones,
    required this.fechaRealizado,
    required this.asignacionId,
  });

  factory ServicioRealizado.fromJson(Map<String, dynamic> json) =>
      _$ServicioRealizadoFromJson(json);

  Map<String, dynamic> toJson() => _$ServicioRealizadoToJson(this);

  @override
  List<Object?> get props => [id, tipoServicio, costoFinal, asignacionId];
}
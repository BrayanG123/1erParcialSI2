import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';

part 'incidente.g.dart';

enum EstadoIncidente {
  disponible,
  @JsonValue('no_disponible')
  noDisponible,
}

@JsonSerializable()
class Incidente extends Equatable {
  final int id;
  final String descripcion;
  @JsonKey(name: 'fecha_hora')
  final DateTime fechaHora;
  final double latitud;
  final double longitud;
  final EstadoIncidente estado;
  @JsonKey(name: 'resumen_ia')
  final String? resumenIa;
  @JsonKey(name: 'cliente_id')
  final int clienteId;
  @JsonKey(name: 'vehiculo_id')
  final int? vehiculoId;
  @JsonKey(name: 'categoria_id')
  final int? categoriaId;

  const Incidente({
    required this.id,
    required this.descripcion,
    required this.fechaHora,
    required this.latitud,
    required this.longitud,
    required this.estado,
    this.resumenIa,
    required this.clienteId,
    this.vehiculoId,
    this.categoriaId,
  });

  factory Incidente.fromJson(Map<String, dynamic> json) =>
      _$IncidenteFromJson(json);

  Map<String, dynamic> toJson() => _$IncidenteToJson(this);

  @override
  List<Object?> get props =>
      [id, descripcion, fechaHora, latitud, longitud, estado, clienteId];
}
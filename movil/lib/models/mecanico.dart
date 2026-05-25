import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';


part 'mecanico.g.dart';


@JsonSerializable()
class Mecanico extends Equatable {
  final int id;
  @JsonKey(name: 'usuario_id')
  final int usuarioId;
  @JsonKey(name: 'taller_id')
  final int? tallerId;
  final String? especialidad;
  final String estado;
  final String? telefono;
  final double? latitud;
  final double? longitud;
  @JsonKey(name: 'foto_vehiculo')
  final String? fotoVehiculo;
  @JsonKey(name: 'tipo_seguro')
  final String? tipoSeguro;

  const Mecanico({
    required this.id,
    required this.usuarioId,
    this.tallerId,
    this.especialidad,
    required this.estado,
    this.telefono,
    this.latitud,
    this.longitud,
    this.fotoVehiculo,
    this.tipoSeguro,
  });

  factory Mecanico.fromJson(Map<String, dynamic> json) =>
      _$MecanicoFromJson(json);

  Map<String, dynamic> toJson() => _$MecanicoToJson(this);

  @override
  List<Object?> get props =>
      [id, usuarioId, tallerId, especialidad, estado, latitud, longitud];
}
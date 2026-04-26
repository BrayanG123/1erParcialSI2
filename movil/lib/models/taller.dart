import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';

part 'taller.g.dart';

@JsonSerializable()
class Taller extends Equatable {
  final int id;
  @JsonKey(name: 'administrador_id')
  final int? administradorId;
  final String nombre;
  final String direccion;
  final double? latitud;
  final double? longitud;
  final String? telefono;
  @JsonKey(name: 'calificacion_promedio')
  final double? calificacionPromedio;

  const Taller({
    required this.id,
    this.administradorId,
    required this.nombre,
    required this.direccion,
    this.latitud,
    this.longitud,
    this.telefono,
    this.calificacionPromedio,
  });

  factory Taller.fromJson(Map<String, dynamic> json) => _$TallerFromJson(json);

  Map<String, dynamic> toJson() => _$TallerToJson(this);

  @override
  List<Object?> get props => [id, nombre, direccion];
}
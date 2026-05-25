import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';

part 'calificacion.g.dart';

@JsonSerializable()
class Calificacion extends Equatable {
  final int id;
  final int puntuacion; // 1 a 5
  final String? comentario;
  final DateTime fecha;
  @JsonKey(name: 'servicio_id')
  final int servicioId;

  const Calificacion({
    required this.id,
    required this.puntuacion,
    this.comentario,
    required this.fecha,
    required this.servicioId,
  });

  factory Calificacion.fromJson(Map<String, dynamic> json) =>
      _$CalificacionFromJson(json);

  Map<String, dynamic> toJson() => _$CalificacionToJson(this);

  @override
  List<Object?> get props => [id, puntuacion, servicioId];
}
import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';

part 'evidencia.g.dart';

enum TipoEvidencia { foto, audio }

@JsonSerializable()
class Evidencia extends Equatable {
  final int id;
  final TipoEvidencia tipo;
  @JsonKey(name: 'url_archivo')
  final String urlArchivo;
  @JsonKey(name: 'fecha_subida')
  final DateTime fechaSubida;
  @JsonKey(name: 'procesado_ia')
  final int procesadoIa; // 0 = no, 1 = sí
  @JsonKey(name: 'incidente_id')
  final int incidenteId;

  const Evidencia({
    required this.id,
    required this.tipo,
    required this.urlArchivo,
    required this.fechaSubida,
    required this.procesadoIa,
    required this.incidenteId,
  });

  factory Evidencia.fromJson(Map<String, dynamic> json) =>
      _$EvidenciaFromJson(json);

  Map<String, dynamic> toJson() => _$EvidenciaToJson(this);

  @override
  List<Object?> get props => [id, tipo, urlArchivo, incidenteId];
}
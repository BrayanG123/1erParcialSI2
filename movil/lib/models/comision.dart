import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';

part 'comision.g.dart';

@JsonSerializable()
class Comision extends Equatable {
  final int id;
  final double porcentaje;
  final double monto;
  @JsonKey(name: 'fecha_emision')
  final DateTime fechaEmision;
  @JsonKey(name: 'fecha_pago')
  final DateTime? fechaPago;
  @JsonKey(name: 'servicio_id')
  final int servicioId;

  const Comision({
    required this.id,
    required this.porcentaje,
    required this.monto,
    required this.fechaEmision,
    this.fechaPago,
    required this.servicioId,
  });

  factory Comision.fromJson(Map<String, dynamic> json) =>
      _$ComisionFromJson(json);

  Map<String, dynamic> toJson() => _$ComisionToJson(this);

  @override
  List<Object?> get props => [id, monto, porcentaje, servicioId];
}
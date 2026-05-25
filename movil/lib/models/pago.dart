import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';

part 'pago.g.dart';

enum EstadoPago { pendiente, pagado }

enum MetodoPago {
  efectivo,
  pasarela,
}

@JsonSerializable()
class Pago extends Equatable {
  final int id;
  final double monto;
  final EstadoPago estado;
  final MetodoPago? metodo;
  final String? referencia;
  @JsonKey(name: 'fecha_pago')
  final DateTime fechaPago;
  @JsonKey(name: 'servicio_id')
  final int servicioId;

  const Pago({
    required this.id,
    required this.monto,
    required this.estado,
    this.metodo,
    this.referencia,
    required this.fechaPago,
    required this.servicioId,
  });

  factory Pago.fromJson(Map<String, dynamic> json) => _$PagoFromJson(json);

  Map<String, dynamic> toJson() => _$PagoToJson(this);

  @override
  List<Object?> get props => [id, monto, estado, servicioId];
}
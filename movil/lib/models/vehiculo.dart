import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';

part 'vehiculo.g.dart';

@JsonSerializable()
class Vehiculo extends Equatable {
  final int id;
  @JsonKey(name: 'cliente_id')
  final int clienteId;
  final String placa;
  final String modelo;
  final String color;
  @JsonKey(name: 'foto_vehiculo')
  final String? fotoVehiculo;
  @JsonKey(name: 'tipo_seguro')
  final String? tipoSeguro;

  const Vehiculo({
    required this.id,
    required this.clienteId,
    required this.placa,
    required this.modelo,
    required this.color,
    this.fotoVehiculo,
    this.tipoSeguro,
  });

  factory Vehiculo.fromJson(Map<String, dynamic> json) =>
      _$VehiculoFromJson(json);

  Map<String, dynamic> toJson() => _$VehiculoToJson(this);

  @override
  List<Object?> get props => [id, clienteId, placa, modelo, color];
}
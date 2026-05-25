import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';

part 'categoria.g.dart';

@JsonSerializable()
class Categoria extends Equatable {
  final int id;
  final String nombre;
  final String? descripcion;

  const Categoria({
    required this.id,
    required this.nombre,
    this.descripcion,
  });

  factory Categoria.fromJson(Map<String, dynamic> json) =>
      _$CategoriaFromJson(json);

  Map<String, dynamic> toJson() => _$CategoriaToJson(this);

  @override
  List<Object?> get props => [id, nombre];
}
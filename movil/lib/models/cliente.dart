import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';

part 'cliente.g.dart';


@JsonSerializable()
class Cliente extends Equatable {
  final int id;
  @JsonKey(name: 'usuario_id')
  final int usuarioId;
  @JsonKey(name: 'foto_perfil')
  final String? fotoPerfil;

  const Cliente({
    required this.id,
    required this.usuarioId,
    this.fotoPerfil,
  });

  factory Cliente.fromJson(Map<String, dynamic> json) =>
      _$ClienteFromJson(json);

  Map<String, dynamic> toJson() => _$ClienteToJson(this);

  @override
  List<Object?> get props => [id, usuarioId, fotoPerfil];
}
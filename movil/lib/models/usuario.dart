
import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';
import 'package:movil/models/rol_usuario.dart';


part 'usuario.g.dart';


@JsonSerializable()
class Usuario extends Equatable {
  final int id;
  final String nombre;
  final String apellido;
  final String email;
  final String username;
  final RolUsuario rol;
  @JsonKey(name: 'is_active')
  final bool isActive;
  @JsonKey(name: 'fecha_creacion')
  final DateTime fechaCreacion;

  const Usuario({
    required this.id,
    required this.nombre,
    required this.apellido,
    required this.email,
    required this.username,
    required this.rol,
    required this.isActive,
    required this.fechaCreacion,
  });

  factory Usuario.fromJson(Map<String, dynamic> json) =>
      _$UsuarioFromJson(json);

  Map<String, dynamic> toJson() => _$UsuarioToJson(this);


  @override
  List<Object?> get props =>
      [id, nombre, apellido, email, username, rol, isActive, fechaCreacion];
}
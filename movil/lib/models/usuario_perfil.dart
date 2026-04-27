import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';
import 'package:movil/models/rol_usuario.dart';

part 'usuario_perfil.g.dart';


// Perfil del cliente embebido en UsuarioConPerfil
@JsonSerializable()
class PerfilCliente extends Equatable {
  final int id;
  @JsonKey(name: 'usuario_id')
  final int usuarioId;
  @JsonKey(name: 'foto_perfil')
  final String? fotoPerfil;

  const PerfilCliente({
    required this.id,
    required this.usuarioId,
    this.fotoPerfil,
  });

  factory PerfilCliente.fromJson(Map<String, dynamic> json) =>
      _$PerfilClienteFromJson(json);

  Map<String, dynamic> toJson() => _$PerfilClienteToJson(this);

  @override
  List<Object?> get props => [id, usuarioId, fotoPerfil];
}


// Perfil del mecánico embebido en UsuarioConPerfil
@JsonSerializable()
class PerfilMecanico extends Equatable {
  final int id;
  @JsonKey(name: 'usuario_id')
  final int usuarioId;
  final String? especialidad;
  final String estado;
  final String? telefono;
  final double? latitud;
  final double? longitud;

  const PerfilMecanico({
    required this.id,
    required this.usuarioId,
    this.especialidad,
    required this.estado,
    this.telefono,
    this.latitud,
    this.longitud,
  });

  factory PerfilMecanico.fromJson(Map<String, dynamic> json) =>
      _$PerfilMecanicoFromJson(json);

  Map<String, dynamic> toJson() => _$PerfilMecanicoToJson(this);

  @override
  List<Object?> get props =>
      [id, usuarioId, especialidad, estado, telefono, latitud, longitud];
}

// Usuario completo con su perfil (cliente o mecánico)
@JsonSerializable()
class UsuarioConPerfil extends Equatable {
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
  @JsonKey(name: 'perfil_cliente')
  final PerfilCliente? perfilCliente;
  @JsonKey(name: 'perfil_mecanico')
  final PerfilMecanico? perfilMecanico;

  const UsuarioConPerfil({
    required this.id,
    required this.nombre,
    required this.apellido,
    required this.email,
    required this.username,
    required this.rol,
    required this.isActive,
    required this.fechaCreacion,
    this.perfilCliente,
    this.perfilMecanico,
  });

  factory UsuarioConPerfil.fromJson(Map<String, dynamic> json) =>
      _$UsuarioConPerfilFromJson(json);

  Map<String, dynamic> toJson() => _$UsuarioConPerfilToJson(this);

  @override
  List<Object?> get props => [
        id, nombre, apellido, email, username, rol,
        isActive, fechaCreacion, perfilCliente, perfilMecanico,
      ];
}
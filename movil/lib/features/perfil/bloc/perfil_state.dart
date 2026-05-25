import 'package:equatable/equatable.dart';
import 'package:movil/models/usuario_perfil.dart';


abstract class PerfilState extends Equatable {
  const PerfilState();

  @override
  List<Object?> get props => [];
}

class PerfilInicial extends PerfilState {}

class PerfilCargando extends PerfilState {}

// Estado principal: datos cargados
class PerfilCargado extends PerfilState {
  final UsuarioConPerfil usuario;

  const PerfilCargado(this.usuario);

  @override
  List<Object?> get props => [usuario];
}

// Se emite después de guardar exitosamente los datos
class PerfilGuardado extends PerfilState {
  final UsuarioConPerfil usuario;

  const PerfilGuardado(this.usuario);

  @override
  List<Object?> get props => [usuario];
}

// Se emite después de cambiar contraseña exitosamente
class PasswordCambiado extends PerfilState {}

class PerfilError extends PerfilState {
  final String mensaje;

  const PerfilError(this.mensaje);

  @override
  List<Object?> get props => [mensaje];
}
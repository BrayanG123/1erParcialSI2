import 'package:equatable/equatable.dart';
import 'package:movil/models/usuario.dart';


abstract class AuthState extends Equatable {
  const AuthState();

  @override
  List<Object?> get props => [];
}


/// Estado inicial: aún no sabemos si hay sesión
class AuthInitial extends AuthState {
  const AuthInitial();
}

/// Verificando si hay token guardado (se usa en SplashScreen)
class AuthLoading extends AuthState {
  const AuthLoading();
}

/// El usuario está autenticado
class AuthAuthenticated extends AuthState {
  final Usuario usuario;

  const AuthAuthenticated(this.usuario);

  @override
  List<Object?> get props => [usuario];
}

/// No hay sesión activa
class AuthUnauthenticated extends AuthState {
  const AuthUnauthenticated();
}

/// Ocurrió un error durante login o registro
class AuthError extends AuthState {
  final String mensaje;

  const AuthError(this.mensaje);

  @override
  List<Object?> get props => [mensaje];
}

/// Registro exitoso (distinto de autenticado: el usuario debe hacer login)
class AuthRegistroExitoso extends AuthState {
  final String mensaje;

  const AuthRegistroExitoso(this.mensaje);

  @override
  List<Object?> get props => [mensaje];
}
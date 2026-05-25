// import 'package:bloc/bloc.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:movil/core/network/api_exception.dart';
import 'package:movil/core/storage/secure_storage.dart';
import 'package:movil/features/auth/bloc/auth_state.dart';
import 'package:movil/features/auth/models/login_request.dart';
import 'package:movil/features/auth/models/registro_cliente_request.dart';
import 'package:movil/features/auth/models/registro_mecanico_request.dart';
import 'package:movil/features/auth/services/auth_service.dart';



class AuthCubit extends Cubit<AuthState>{

  final AuthService _authService;

  AuthCubit({AuthService? authService})
      : _authService = authService ?? AuthService(),
        super(const AuthInitial());

  /// Llamado al iniciar la app: comprueba si hay token guardado.
  /// Si lo hay, obtiene el perfil del usuario; si no, va a la pantalla de login.
  Future<void> verificarSesion() async {
    emit(const AuthLoading());
    try {
      final hayToken = await SecureStorage.hayToken();
      if (!hayToken) {
        emit(const AuthUnauthenticated());
        return;
      }
      final usuario = await _authService.obtenerPerfil();
      emit(AuthAuthenticated(usuario));
    } on ApiException catch (_) {
      // Token expirado o inválido
      await SecureStorage.eliminarToken();
      emit(const AuthUnauthenticated());
    } catch (_) {
      emit(const AuthUnauthenticated());
    }
  }

  /// Inicia sesión con username y password
  Future<void> login(String username, String password) async {
    emit(const AuthLoading());
    try {
      final usuario = await _authService.login(
        LoginRequest(username: username, password: password),
      );
      emit(AuthAuthenticated(usuario));
    } on ApiException catch (e) {
      emit(AuthError(e.mensaje));
    } catch (_) {
      emit(const AuthError('Error inesperado. Intenta de nuevo.'));
    }
  }

  /// Registra un nuevo cliente
  Future<void> registrarCliente(RegistroClienteRequest request) async {
    emit(const AuthLoading());
    try {
      await _authService.registrarCliente(request);
      emit(const AuthRegistroExitoso(
        '¡Cuenta creada! Ahora inicia sesión.',
      ));
    } on ApiException catch (e) {
      emit(AuthError(e.mensaje));
    } catch (_) {
      emit(const AuthError('Error inesperado. Intenta de nuevo.'));
    }
  }

  /// Registra un nuevo mecánico
  Future<void> registrarMecanico(RegistroMecanicoRequest request) async {
    emit(const AuthLoading());
    try {
      await _authService.registrarMecanico(request);
      emit(const AuthRegistroExitoso(
        '¡Solicitud enviada! Un administrador revisará tu cuenta.',
      ));
    } on ApiException catch (e) {
      emit(AuthError(e.mensaje));
    } catch (_) {
      emit(const AuthError('Error inesperado. Intenta de nuevo.'));
    }
  }

  /// Cierra la sesión
  Future<void> logout() async {
    await _authService.logout();
    emit(const AuthUnauthenticated());
  }

}
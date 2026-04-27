import 'package:dio/dio.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:movil/features/perfil/bloc/perfil_state.dart';
import 'package:movil/features/perfil/services/perfil_service.dart';



class PerfilCubit extends Cubit<PerfilState> {
  final PerfilService _service;

  PerfilCubit({PerfilService? service})
      : _service = service ?? PerfilService(),
        super(PerfilInicial());

  /// Carga los datos del usuario desde el backend
  Future<void> cargar() async {
    emit(PerfilCargando());
    try {
      final usuario = await _service.obtenerPerfil();
      emit(PerfilCargado(usuario));
    } on DioException catch (e) {
      emit(PerfilError(e.response?.data['detail'] ?? 'Error al cargar perfil'));
    }
  }

  /// Actualiza nombre, apellido y/o username
  Future<void> guardar({
    required String nombre,
    required String apellido,
    required String username,
  }) async {
    final estadoActual = state;
    if (estadoActual is! PerfilCargado) return;

    emit(PerfilCargando());
    try {
      await _service.actualizarPerfil(
        nombre: nombre,
        apellido: apellido,
        username: username,
      );
      // Recargamos para tener los datos actualizados del server
      final usuarioActualizado = await _service.obtenerPerfil();
      emit(PerfilGuardado(usuarioActualizado));
    } on DioException catch (e) {
      emit(PerfilError(e.response?.data['detail'] ?? 'Error al guardar'));
    }
  }

  /// Cambia la contraseña
  Future<void> cambiarPassword({
    required String actual,
    required String nuevo,
  }) async {
    if (state is! PerfilCargado && state is! PerfilGuardado) return;

    emit(PerfilCargando());
    try {
      await _service.cambiarPassword(
        passwordActual: actual,
        passwordNuevo: nuevo,
      );
      emit(PasswordCambiado());
    } on DioException catch (e) {
      emit(PerfilError(e.response?.data['detail'] ?? 'Error al cambiar contraseña'));
    }
  }
}
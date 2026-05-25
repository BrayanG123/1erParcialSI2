import 'package:movil/core/network/api_client.dart';
import 'package:movil/core/constants/api_constants.dart';
import 'package:movil/models/usuario_perfil.dart';


class PerfilService {
  final _dio = ApiClient.dio;

  /// Obtiene los datos del usuario autenticado con su perfil
  Future<UsuarioConPerfil> obtenerPerfil() async {
    final response = await _dio.get('${ApiConstants.usuarios}/me');
    return UsuarioConPerfil.fromJson(response.data as Map<String, dynamic>);
  }

  /// Actualiza nombre, apellido y/o username del usuario
  Future<void> actualizarPerfil({
    String? nombre,
    String? apellido,
    String? username,
  }) async {
    final body = <String, dynamic>{};
    if (nombre != null) body['nombre'] = nombre;
    if (apellido != null) body['apellido'] = apellido;
    if (username != null) body['username'] = username;

    await _dio.patch('${ApiConstants.usuarios}/me', data: body);
  }

  /// Cambia la contraseña del usuario autenticado
  Future<void> cambiarPassword({
    required String passwordActual,
    required String passwordNuevo,
  }) async {
    await _dio.patch(
      '${ApiConstants.usuarios}/me/password',
      data: {
        'password_actual': passwordActual,
        'password_nuevo': passwordNuevo,
      },
    );
  }
}
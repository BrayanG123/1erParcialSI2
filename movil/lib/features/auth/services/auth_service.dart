import 'package:dio/dio.dart';
import 'package:movil/core/network/api_client.dart';
import 'package:movil/core/network/api_exception.dart';
import 'package:movil/core/constants/api_constants.dart';
import 'package:movil/core/storage/secure_storage.dart';
import 'package:movil/models/usuario.dart';
import 'package:movil/features/auth/models/login_request.dart';
import 'package:movil/features/auth/models/login_response.dart';
import 'package:movil/features/auth/models/registro_cliente_request.dart';
import 'package:movil/features/auth/models/registro_mecanico_request.dart';



class AuthService {

  final Dio _dio = ApiClient.dio;


  /// Login con OAuth2 form-data. Guarda el token y devuelve el usuario.
  Future<Usuario> login(LoginRequest request) async {
    try {
      // 1. Obtener el token
      final tokenResponse = await _dio.post(
        ApiConstants.login,
        data: FormData.fromMap(request.toFormData()),
        options: Options(contentType: 'application/x-www-form-urlencoded'),
      );
      final loginResp = LoginResponse.fromJson(tokenResponse.data);

      // 2. Guardar el token de forma segura
      await SecureStorage.guardarToken(loginResp.accessToken);

      // 3. Obtener el perfil del usuario autenticado
      final userResponse = await _dio.get(ApiConstants.usuarioMe);
      return Usuario.fromJson(userResponse.data);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }


  /// Registro de cliente. Devuelve el usuario creado.
  Future<Usuario> registrarCliente(RegistroClienteRequest request) async {
    try {
      final response = await _dio.post(
        ApiConstants.registerCliente,
        data: request.toJson(),
      );
      return Usuario.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }


  /// Registro de mecánico. Devuelve el usuario creado.
  Future<Usuario> registrarMecanico(RegistroMecanicoRequest request) async {
    try {
      final response = await _dio.post(
        ApiConstants.registerMecanico,
        data: request.toJson(),
      );
      return Usuario.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }


  /// Cierra sesión: elimina el token local.
  Future<void> logout() async {
    await SecureStorage.eliminarToken();
  }

  /// Obtiene el perfil del usuario actualmente autenticado.
  Future<Usuario> obtenerPerfil() async {
    try {
      final response = await _dio.get(ApiConstants.usuarioMe);
      return Usuario.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }
}
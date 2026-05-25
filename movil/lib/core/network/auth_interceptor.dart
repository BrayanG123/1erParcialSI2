import 'package:dio/dio.dart';
import 'package:movil/core/storage/secure_storage.dart';

class AuthInterceptor extends Interceptor {
  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await SecureStorage.leerToken();

    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }

    return handler.next(options); // continúa con la petición
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    if (err.response?.statusCode == 401) {
      // Token inválido o expirado: limpia la sesión local
      SecureStorage.eliminarToken();
    }
    return handler.next(err); // propaga el error para que el servicio lo maneje
  }
}
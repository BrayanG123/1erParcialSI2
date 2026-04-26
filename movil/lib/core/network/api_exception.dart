import 'package:dio/dio.dart';

class ApiException implements Exception {
  final String mensaje;
  final int? statusCode;

  const ApiException({required this.mensaje, this.statusCode});

  /// Convierte un DioException en un ApiException con mensaje en español
  factory ApiException.fromDioException(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return const ApiException(
          mensaje: 'El servidor tardó demasiado en responder. Intenta de nuevo.',
        );

      case DioExceptionType.badResponse:
        final statusCode = e.response?.statusCode;
        final detalle = _extraerDetalle(e.response?.data);

        return switch (statusCode) {
          400 => ApiException(mensaje: detalle ?? 'Datos inválidos.', statusCode: 400),
          401 => const ApiException(mensaje: 'Sesión expirada. Inicia sesión de nuevo.', statusCode: 401),
          403 => const ApiException(mensaje: 'No tienes permiso para realizar esta acción.', statusCode: 403),
          404 => const ApiException(mensaje: 'El recurso solicitado no existe.', statusCode: 404),
          422 => ApiException(mensaje: detalle ?? 'Error de validación.', statusCode: 422),
          500 => const ApiException(mensaje: 'Error interno del servidor.', statusCode: 500),
          _   => ApiException(mensaje: detalle ?? 'Error desconocido ($statusCode).', statusCode: statusCode),
        };

      case DioExceptionType.connectionError:
        return const ApiException(
          mensaje: 'Sin conexión. Verifica tu internet.',
        );

      default:
        return ApiException(mensaje: e.message ?? 'Error de red.');
    }
  }

  /// Extrae el campo "detail" que devuelve FastAPI en los errores
  static String? _extraerDetalle(dynamic data) {
    if (data == null) return null;
    if (data is Map) return data['detail']?.toString();
    return data.toString();
  }

  @override
  String toString() => 'ApiException(statusCode: $statusCode, mensaje: $mensaje)';
}
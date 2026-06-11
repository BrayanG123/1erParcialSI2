import 'package:dio/dio.dart';
import 'package:movil/core/constants/api_constants.dart';
import 'package:movil/core/network/api_client.dart';
import 'package:movil/core/network/api_exception.dart';
import 'package:movil/models/pago.dart';


class PagoService {
  final Dio _dio = ApiClient.dio;

  /// Registra el pago de un servicio (el cliente elige el método).
  Future<Pago> registrarPago({
    required int servicioId,
    required MetodoPago metodo,
  }) async {
    final metodoStr = metodo == MetodoPago.efectivo ? 'efectivo' : 'pasarela';
    try {
      final response = await _dio.post(
        ApiConstants.pagos,
        data: {
          'servicio_id': servicioId,
          'metodo':      metodoStr,
        },
      );
      return Pago.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  /// Consulta si ya existe un pago para el servicio.
  Future<Pago> obtenerPorServicio(int servicioId) async {
    try {
      final response = await _dio.get(
        '${ApiConstants.pagos}/servicio/$servicioId',
      );
      return Pago.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  // ── Stripe ────────────────────────────────────────────────────────────

  /// Crea la sesión de Stripe Checkout en el backend.
  /// Devuelve {pago_id, session_id, checkout_url}.
  Future<Map<String, dynamic>> crearCheckoutStripe(int servicioId) async {
    try {
      final response = await _dio.post(
        '${ApiConstants.pagos}/stripe/checkout',
        data: {'servicio_id': servicioId},
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  /// Verifica contra Stripe si la sesión ya fue pagada.
  /// El backend consulta a Stripe directamente (no depende del webhook).
  /// Devuelve el pago con su estado actual.
  Future<Pago> confirmarPagoStripe(int pagoId) async {
    try {
      final response = await _dio.post(
        '${ApiConstants.pagos}/stripe/confirmar/$pagoId',
      );
      return Pago.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }
}
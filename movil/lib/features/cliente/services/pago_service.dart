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
}
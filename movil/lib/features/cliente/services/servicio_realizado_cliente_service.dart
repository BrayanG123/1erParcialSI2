import 'package:dio/dio.dart';
import 'package:movil/core/constants/api_constants.dart';
import 'package:movil/core/network/api_client.dart';
import 'package:movil/core/network/api_exception.dart';
import 'package:movil/models/servicio_realizado.dart';


class ServicioRealizadoClienteService {
  final Dio _dio = ApiClient.dio;

  Future<ServicioRealizado> obtenerPorAsignacion(int asignacionId) async {
    try {
      final response = await _dio.get(
        '${ApiConstants.serviciosRealizados}/mi-asignacion/$asignacionId',
      );
      return ServicioRealizado.fromJson(
          response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }
}
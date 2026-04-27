import 'package:dio/dio.dart';
import 'package:movil/core/constants/api_constants.dart';
import 'package:movil/core/network/api_client.dart';
import 'package:movil/core/network/api_exception.dart';
import 'package:movil/models/asignacion_servicio.dart';


class AsignacionClienteService {
  final Dio _dio = ApiClient.dio;

  /// Retorna la asignación asociada al incidente del cliente.
  /// Lanza [ApiException] si el incidente aún no tiene asignación (404).
  Future<AsignacionServicio> obtenerPorIncidente(int incidenteId) async {
    try {
      final response = await _dio.get(
        '${ApiConstants.incidentes}/$incidenteId/asignacion',
      );
      return AsignacionServicio.fromJson(
          response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }
}
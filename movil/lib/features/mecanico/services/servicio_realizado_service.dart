import 'package:dio/dio.dart';
import 'package:movil/core/constants/api_constants.dart';
import 'package:movil/core/network/api_client.dart';
import 'package:movil/core/network/api_exception.dart';
import 'package:movil/models/servicio_realizado.dart';



class ServicioRealizadoService {
  final Dio _dio = ApiClient.dio;


   /// Registra el servicio completado cuando la asignación queda en "completada".
  Future<ServicioRealizado> registrar({
    required String tipoServicio,
    required String descripcionTrabajo,
    required double costoFinal,
    String? observaciones,
    required int asignacionId,
  }) async {
    try {
      final response = await _dio.post(
        ApiConstants.serviciosRealizados,
        data: {
          'tipo_servicio':       tipoServicio,
          'descripcion_trabajo': descripcionTrabajo,
          'costo_final':         costoFinal,
          'asignacion_id':       asignacionId,
          if (observaciones != null && observaciones.isNotEmpty)
            'observaciones': observaciones,
        },
      );
      return ServicioRealizado.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }
}
import 'package:dio/dio.dart';
import 'package:movil/core/constants/api_constants.dart';
import 'package:movil/core/network/api_client.dart';
import 'package:movil/core/network/api_exception.dart';
import 'package:movil/models/calificacion.dart';


class CalificacionService {
  final Dio _dio = ApiClient.dio;

  Future<Calificacion> calificar({
    required int servicioId,
    required int puntuacion,
    String? comentario,
  }) async {
    try {
      final response = await _dio.post(
        ApiConstants.calificaciones,
        data: {
          'servicio_id': servicioId,
          'puntuacion':  puntuacion,
          if (comentario != null && comentario.isNotEmpty)
            'comentario': comentario,
        },
      );
      return Calificacion.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<Calificacion> obtenerPorServicio(int servicioId) async {
    try {
      final response = await _dio.get(
        '${ApiConstants.calificaciones}/servicio/$servicioId',
      );
      return Calificacion.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }
}
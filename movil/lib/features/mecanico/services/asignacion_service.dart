import 'package:dio/dio.dart';
import 'package:movil/core/constants/api_constants.dart';
import 'package:movil/core/network/api_client.dart';
import 'package:movil/core/network/api_exception.dart';
import 'package:movil/models/asignacion_servicio.dart';


class AsignacionService {

  final Dio _dio = ApiClient.dio;

  /// Devuelve todas las asignaciones del mecánico autenticado.
  Future<List<AsignacionServicio>> obtenerMisAsignaciones() async {
    try {
      final response = await _dio.get('${ApiConstants.asignaciones}/mis-asignaciones');
      final lista = response.data as List<dynamic>;
      return lista
          .map((json) => AsignacionServicio.fromJson(json as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  /// Obtiene una asignación por su ID.
  Future<AsignacionServicio> obtenerPorId(int id) async {
    try {
      final response = await _dio.get('${ApiConstants.asignaciones}/$id');
      return AsignacionServicio.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  /// Avanza al siguiente estado: aceptada → en_camino → en_servicio → completada.
  /// El mecánico solo puede avanzar hacia adelante; 
  Future<AsignacionServicio> avanzarEstado(int id, EstadoAsignacion nuevoEstado) async {
    final estadoStr = switch (nuevoEstado) {
      EstadoAsignacion.enCamino   => 'en_camino',
      EstadoAsignacion.enAtencion => 'en_atencion',
      EstadoAsignacion.finalizado => 'finalizado',
      _                           => nuevoEstado.name,
    };
    try {
      final response = await _dio.patch(
        '${ApiConstants.asignaciones}/$id/estado',
        data: {'estado': estadoStr},
      );
      return AsignacionServicio.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }
}
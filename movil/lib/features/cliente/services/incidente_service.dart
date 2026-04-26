import 'package:dio/dio.dart';
import 'package:movil/core/constants/api_constants.dart';
import 'package:movil/core/network/api_client.dart';
import 'package:movil/core/network/api_exception.dart';
import 'package:movil/models/incidente.dart';



class IncidenteService {
  final Dio _dio = ApiClient.dio;

  /// Crea un nuevo incidente (solicitud de auxilio).
  Future<Incidente> crearIncidente({
    required String descripcion,
    required double latitud,
    required double longitud,
    required int clienteId,
    int? vehiculoId,
    int? categoriaId,
  }) async {
    try {
      final response = await _dio.post(
        ApiConstants.incidentes,
        data: {
          'descripcion':  descripcion,
          'latitud':      latitud,
          'longitud':     longitud,
          'cliente_id':   clienteId,
          if (vehiculoId  != null) 'vehiculo_id':  vehiculoId,
          if (categoriaId != null) 'categoria_id': categoriaId,
        },
      );
      return Incidente.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  /// Obtiene los incidentes del cliente autenticado.
  Future<List<Incidente>> obtenerMisIncidentes() async {
    try {
      final response = await _dio.get(ApiConstants.incidentes);
      final lista = response.data as List<dynamic>;
      return lista
          .map((json) => Incidente.fromJson(json as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }
}
import 'package:dio/dio.dart';
import 'package:movil/core/constants/api_constants.dart';
import 'package:movil/core/network/api_client.dart';
import 'package:movil/core/network/api_exception.dart';
import 'package:movil/models/vehiculo.dart';



class VehiculoService {
  final Dio _dio = ApiClient.dio;


  // ── Listar mis vehículos 
  Future<List<Vehiculo>> obtenerMisVehiculos() async {
    try {
      final response = await _dio.get(ApiConstants.vehiculos);
      final lista = response.data as List<dynamic>;
      return lista
          .map((j) => Vehiculo.fromJson(j as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }


  // ── Crear
  Future<Vehiculo> crear({
    required String placa,
    required String modelo,
    required String color,
    String? tipoSeguro,
  }) async {
    try {
      final response = await _dio.post(
        ApiConstants.vehiculos,
        data: {
          'placa': placa,
          'modelo': modelo,
          'color': color,
          if (tipoSeguro != null && tipoSeguro.isNotEmpty)
            'tipo_seguro': tipoSeguro,
        },
      );
      return Vehiculo.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  // ── Actualizar datos
  Future<Vehiculo> actualizar({
    required int id,
    String? modelo,
    String? color,
    String? tipoSeguro,
  }) async {
    try {
      final response = await _dio.patch(
        '${ApiConstants.vehiculos}/$id',
        data: {
          if (modelo != null) 'modelo': modelo,
          if (color != null) 'color': color,
          if (tipoSeguro != null) 'tipo_seguro': tipoSeguro,
        },
      );
      return Vehiculo.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  // ── Subir foto ───
  Future<Vehiculo> subirFoto({
    required int id,
    required String rutaFoto,
  }) async {
    try {
      final formData = FormData.fromMap({
        'foto': await MultipartFile.fromFile(
          rutaFoto,
          filename: rutaFoto.split('/').last,
        ),
      });
      final response = await _dio.post(
        '${ApiConstants.vehiculos}/$id/foto',
        data: formData,
      );
      return Vehiculo.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }


  // ── Eliminar ─
  Future<void> eliminar(int id) async {
    try {
      await _dio.delete('${ApiConstants.vehiculos}/$id');
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

}
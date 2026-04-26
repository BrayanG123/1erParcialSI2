import 'package:dio/dio.dart';
import 'package:movil/core/constants/api_constants.dart';
import 'package:movil/core/network/api_client.dart';
import 'package:movil/core/network/api_exception.dart';
import 'package:movil/models/vehiculo.dart';


class VehiculoService {
  final Dio _dio = ApiClient.dio;

  Future<List<Vehiculo>> obtenerMisVehiculos() async {
    try {
      final response = await _dio.get(ApiConstants.vehiculos);
      final lista = response.data as List<dynamic>;
      return lista.map((json) => Vehiculo.fromJson(json as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }
}
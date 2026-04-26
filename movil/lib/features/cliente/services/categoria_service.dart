import 'package:dio/dio.dart';
import 'package:movil/core/constants/api_constants.dart';
import 'package:movil/core/network/api_client.dart';
import 'package:movil/core/network/api_exception.dart';
import 'package:movil/models/categoria.dart';

class CategoriaService {
  final Dio _dio = ApiClient.dio;

  /// Devuelve todas las categorías de servicio disponibles.
  Future<List<Categoria>> obtenerCategorias() async {
    try {
      final response = await _dio.get(ApiConstants.categorias);
      final lista = response.data as List<dynamic>;
      return lista.map((json) => Categoria.fromJson(json as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }
}
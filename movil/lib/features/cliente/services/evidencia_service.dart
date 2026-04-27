import 'package:dio/dio.dart';
import 'package:movil/core/constants/api_constants.dart';
import 'package:movil/core/network/api_client.dart';
import 'package:movil/core/network/api_exception.dart';
import 'package:movil/models/evidencia.dart';


class EvidenciaService {
  final Dio _dio = ApiClient.dio;

  Future<Evidencia> subirFoto(int incidenteId, String rutaFoto) async {
    try {
      final resp = await _dio.post(
        '${ApiConstants.evidencias}/incidente/$incidenteId/foto',
        data: FormData.fromMap({
          'foto': await MultipartFile.fromFile(
            rutaFoto,
            filename: rutaFoto.split('/').last,
          ),
        }),
      );
      return Evidencia.fromJson(resp.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<List<Evidencia>> listar(int incidenteId) async {
    try {
      final resp = await _dio
          .get('${ApiConstants.evidencias}/incidente/$incidenteId');
      return (resp.data as List)
          .map((j) => Evidencia.fromJson(j as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }
}
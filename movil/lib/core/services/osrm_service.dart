import 'package:dio/dio.dart';
import 'package:latlong2/latlong.dart';


class OsrmService {

  // API pública de OSRM — sin clave, gratuita
  static const _baseUrl = 'https://router.project-osrm.org/route/v1/driving';


  final Dio _dio;

  OsrmService({Dio? dio})
      : _dio = dio ??
            Dio(BaseOptions(
              connectTimeout: const Duration(seconds: 10),
              receiveTimeout: const Duration(seconds: 15),
            ));

  /// Devuelve la lista de puntos que forman la ruta entre [origen] y [destino].
  /// Retorna `[]` si la ruta no pudo calcularse.
  Future<List<LatLng>> obtenerRuta({
    required LatLng origen,
    required LatLng destino,
  }) async {
    try {
      // OSRM recibe coordenadas como lon,lat (nota el orden: lon primero)
      final url =
          '$_baseUrl/${origen.longitude},${origen.latitude};'
          '${destino.longitude},${destino.latitude}'
          '?overview=full&geometries=geojson';

      final response = await _dio.get(url);

      if (response.statusCode != 200) return [];

      final data = response.data as Map<String, dynamic>;
      final routes = data['routes'] as List<dynamic>?;
      if (routes == null || routes.isEmpty) return [];

      final geometry = routes[0]['geometry'] as Map<String, dynamic>;
      final coords = geometry['coordinates'] as List<dynamic>;

      // GeoJSON: cada punto es [lon, lat]
      return coords
          .map((c) => LatLng(
                (c[1] as num).toDouble(),
                (c[0] as num).toDouble(),
              ))
          .toList();

    } catch (_) {
      return [];
    }

  }


}
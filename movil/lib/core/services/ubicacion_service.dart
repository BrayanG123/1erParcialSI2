import 'package:geolocator/geolocator.dart';



class UbicacionService {

  /// Solicita permiso y devuelve la posición actual del dispositivo.
  ///
  /// Lanza [Exception] con mensaje en español si:
  /// - El GPS está apagado.
  /// - El usuario deniega el permiso.
  /// - El permiso fue denegado permanentemente.
  Future<Position> obtenerPosicionActual() async {
    final servicioActivo = await Geolocator.isLocationServiceEnabled();
    if (!servicioActivo) {
      throw Exception('El GPS está desactivado. Actívalo e intenta de nuevo.');
    }

    LocationPermission permiso = await Geolocator.checkPermission();
    if (permiso == LocationPermission.denied) {
      permiso = await Geolocator.requestPermission();
      if (permiso == LocationPermission.denied) {
        throw Exception('Permiso de ubicación denegado.');
      }
    }

    if (permiso == LocationPermission.deniedForever) {
      throw Exception(
        'Permiso de ubicación denegado permanentemente. '
        'Habilítalo en Configuración > Aplicaciones > movil > Permisos.',
      );
    }

    return Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.high,
      ),
    );

  }
}
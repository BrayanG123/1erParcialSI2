import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:movil/config/theme.dart';
import 'package:movil/core/constants/app_constants.dart';
import 'package:movil/core/services/ubicacion_service.dart';


class MapaSelector extends StatefulWidget{
  /// Posición inicial del marcador (opcional).
  final LatLng? posicionInicial;

  /// Se llama cada vez que el usuario selecciona una posición.
  final void Function(double latitud, double longitud) onPosicionSeleccionada;

  const MapaSelector({
    super.key,
    this.posicionInicial,
    required this.onPosicionSeleccionada,
  });

  @override
  State<MapaSelector> createState() => _MapaSelectorState();
}


class _MapaSelectorState extends State<MapaSelector> {

  final MapController _mapController = MapController();
  final _ubicacionService = UbicacionService();

  LatLng? _marcador;
  bool _cargandoGps = false;

  // Centro inicial: La Paz, Bolivia
  static const _defaultCenter = LatLng(-16.5000, -68.1500);

  @override
  void initState() {
    super.initState();
    _marcador = widget.posicionInicial;
  }

  // Obtiene la posición GPS y mueve la cámara al punto.
  Future<void> _usarMiUbicacion() async {
    setState(() => _cargandoGps = true);
    try {
      final pos = await _ubicacionService.obtenerPosicionActual();
      final punto = LatLng(pos.latitude, pos.longitude);
      setState(() => _marcador = punto);
      _mapController.move(punto, AppConstants.zoomMapa);
      widget.onPosicionSeleccionada(pos.latitude, pos.longitude);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(e.toString().replaceFirst('Exception: ', '')),
            backgroundColor: AppTheme.peligro,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _cargandoGps = false);
    }
  }

  /// El usuario toca el mapa: coloca el marcador en ese punto.
  void _onMapTap(TapPosition _, LatLng punto) {
    setState(() => _marcador = punto);
    widget.onPosicionSeleccionada(punto.latitude, punto.longitude);
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // --- Mapa OpenStreetMap ---
        FlutterMap(
          mapController: _mapController,
          options: MapOptions(
            initialCenter: _marcador ?? _defaultCenter,
            initialZoom: AppConstants.zoomMapa,
            onTap: _onMapTap,
          ),
          children: [
            // Tiles gratuitos de OpenStreetMap
            TileLayer(
              urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
              userAgentPackageName: 'com.example.movil',
            ),

            // Marcador de posición seleccionada
            if (_marcador != null)
              MarkerLayer(
                markers: [
                  Marker(
                    point: _marcador!,
                    width: 44,
                    height: 44,
                    child: const Icon(
                      Icons.location_pin,
                      color: Colors.red,
                      size: 44,
                    ),
                  ),
                ],
              ),
          ],
        ),

        // --- Instrucción en la parte superior ---
        Positioned(
          top: 10,
          left: 12,
          right: 12,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.92),
              borderRadius: BorderRadius.circular(8),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.1),
                  blurRadius: 4,
                ),
              ],
            ),
            child: const Text(
              'Toca el mapa para marcar tu ubicación',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12),
            ),
          ),
        ),

        // --- Botón GPS ---
        Positioned(
          bottom: 16,
          right: 16,
          child: FloatingActionButton.small(
            heroTag: 'btn_gps',
            onPressed: _cargandoGps ? null : _usarMiUbicacion,
            backgroundColor: AppTheme.primario,
            tooltip: 'Usar mi ubicación',
            child: _cargandoGps
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                        strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.my_location, color: Colors.white),
          ),
        ),
      ],
    );
  }

  @override
  void dispose() {
    _mapController.dispose();
    super.dispose();
  }


}
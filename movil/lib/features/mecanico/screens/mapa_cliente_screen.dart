// Pantalla de mapa para el MECÁNICO:
//  - Muestra la ubicación del cliente (del incidente) con un marcador rojo.
//  - Muestra la posición actual del mecánico con un marcador azul.
//  - Si la asignación está activa (en_camino / en_atencion), envía la posición
//    del mecánico por WebSocket cada 5 segundos — el cliente la ve en su
//    pantalla de tracking en tiempo real.
//  - Botón para abrir la ruta en Google Maps.

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:geolocator/geolocator.dart';
import 'package:latlong2/latlong.dart';
import 'package:movil/config/theme.dart';
import 'package:movil/features/cliente/services/websocket_service.dart';
import 'package:movil/models/asignacion_servicio.dart';
import 'package:url_launcher/url_launcher.dart';

class MapaClienteScreen extends StatefulWidget {
  final AsignacionServicio asignacion;

  const MapaClienteScreen({super.key, required this.asignacion});

  @override
  State<MapaClienteScreen> createState() => _MapaClienteScreenState();
}

class _MapaClienteScreenState extends State<MapaClienteScreen> {
  final _mapController = MapController();
  final _wsService = WebSocketService();

  LatLng? _posicionMecanico;
  Timer? _timerEnvio;
  StreamSubscription<Position>? _gpsSub;

  LatLng get _posicionCliente => LatLng(
        widget.asignacion.incidente?.latitud ?? -17.7833,
        widget.asignacion.incidente?.longitud ?? -63.1812,
      );

  bool get _trackingActivo =>
      widget.asignacion.estado == EstadoAsignacion.enCamino ||
      widget.asignacion.estado == EstadoAsignacion.enAtencion;

  @override
  void initState() {
    super.initState();
    _iniciarGps();
    if (_trackingActivo && widget.asignacion.mecanicoId != null) {
      _iniciarTracking();
    }
  }

  @override
  void dispose() {
    _timerEnvio?.cancel();
    _gpsSub?.cancel();
    _wsService.desconectar();
    super.dispose();
  }

  Future<void> _iniciarGps() async {
    var permiso = await Geolocator.checkPermission();
    if (permiso == LocationPermission.denied) {
      permiso = await Geolocator.requestPermission();
    }
    if (permiso == LocationPermission.denied ||
        permiso == LocationPermission.deniedForever) {
      return; // sin permiso: el mapa igual muestra al cliente
    }

    // Posición inicial
    try {
      final pos = await Geolocator.getCurrentPosition();
      if (mounted) {
        setState(() => _posicionMecanico = LatLng(pos.latitude, pos.longitude));
      }
    } catch (_) {}

    // Stream de actualizaciones (cada ~10 metros de movimiento)
    _gpsSub = Geolocator.getPositionStream(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: 10,
      ),
    ).listen((pos) {
      if (mounted) {
        setState(() => _posicionMecanico = LatLng(pos.latitude, pos.longitude));
      }
    });
  }

  void _iniciarTracking() {
    // Conecta al canal del incidente como mecánico
    _wsService.conectar(
      incidenteId: widget.asignacion.incidenteId,
      rol: 'mecanico',
      mecanicoId: widget.asignacion.mecanicoId,
    );

    // Envía la última posición conocida cada 5 segundos
    _timerEnvio = Timer.periodic(const Duration(seconds: 5), (_) {
      final pos = _posicionMecanico;
      if (pos == null) return;
      _wsService.enviarMensaje({
        'tipo': 'ubicacion',
        'lat': pos.latitude,
        'lng': pos.longitude,
      });
    });
  }

  Future<void> _abrirEnGoogleMaps() async {
    final destino = _posicionCliente;
    final url = Uri.parse(
      'https://www.google.com/maps/dir/?api=1'
      '&destination=${destino.latitude},${destino.longitude}'
      '&travelmode=driving',
    );
    try {
      await launchUrl(url, mode: LaunchMode.externalApplication);
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No se pudo abrir Google Maps')),
        );
      }
    }
  }

  void _centrarEnCliente() =>
      _mapController.move(_posicionCliente, 15);

  void _centrarEnMecanico() {
    if (_posicionMecanico != null) {
      _mapController.move(_posicionMecanico!, 15);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Ubicación del cliente')),
      body: Stack(
        children: [
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: _posicionCliente,
              initialZoom: 14,
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.example.movil',
              ),
              MarkerLayer(
                markers: [
                  // Cliente (rojo)
                  Marker(
                    point: _posicionCliente,
                    width: 44,
                    height: 44,
                    child: const Icon(Icons.location_pin,
                        size: 44, color: AppTheme.peligro),
                  ),
                  // Mecánico (azul)
                  if (_posicionMecanico != null)
                    Marker(
                      point: _posicionMecanico!,
                      width: 40,
                      height: 40,
                      child: const Icon(Icons.navigation,
                          size: 36, color: AppTheme.primario),
                    ),
                ],
              ),
            ],
          ),

          // Indicador de tracking activo
          if (_trackingActivo)
            Positioned(
              top: 12,
              left: 12,
              right: 12,
              child: Card(
                color: Colors.green.shade50,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12)),
                child: const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  child: Row(
                    children: [
                      Icon(Icons.podcasts, color: Colors.green, size: 18),
                      SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'Compartiendo tu ubicación con el cliente',
                          style: TextStyle(fontSize: 12),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),

          // Botones flotantes de centrado
          Positioned(
            right: 12,
            bottom: 110,
            child: Column(
              children: [
                FloatingActionButton.small(
                  heroTag: 'centrar-cliente',
                  backgroundColor: Colors.white,
                  onPressed: _centrarEnCliente,
                  child: const Icon(Icons.person_pin_circle,
                      color: AppTheme.peligro),
                ),
                const SizedBox(height: 8),
                FloatingActionButton.small(
                  heroTag: 'centrar-mecanico',
                  backgroundColor: Colors.white,
                  onPressed: _centrarEnMecanico,
                  child: const Icon(Icons.navigation, color: AppTheme.primario),
                ),
              ],
            ),
          ),
        ],
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
          child: FilledButton.icon(
            onPressed: _abrirEnGoogleMaps,
            icon: const Icon(Icons.directions),
            label: const Text('Abrir ruta en Google Maps'),
            style: FilledButton.styleFrom(
              minimumSize: const Size.fromHeight(50),
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14)),
            ),
          ),
        ),
      ),
    );
  }
}

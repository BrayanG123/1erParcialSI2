// Recibe el incidenteId como argumento de navegación.
// Se conecta al WebSocket al cargar, muestra el mapa con el marcador del mecánico
// y actualiza el estado automáticamente al recibir mensajes.


import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:movil/config/app_config.dart';
import 'package:movil/features/cliente/services/websocket_service.dart';
import 'package:dio/dio.dart';



// Coordenadas de Santa Cruz de la Sierra como posición inicial del mapa
const _latInicial = -17.7833;
const _lngInicial = -63.1812;

class TrackingIncidenteScreen extends StatefulWidget {
  final int incidenteId;

  const TrackingIncidenteScreen({super.key, required this.incidenteId});

  @override
  State<TrackingIncidenteScreen> createState() =>
      _TrackingIncidenteScreenState();
}

class _TrackingIncidenteScreenState extends State<TrackingIncidenteScreen> {

  // ── WebSocket ──────────────────────────────────────────────────────────────
  late final WebSocketService _wsService;
  StreamSubscription<Map<String, dynamic>>? _wsSub;

  // ── Estado de la UI ────────────────────────────────────────────────────────
  LatLng? _posicionMecanico;      // null = mecánico aún no envió posición
  String _estadoServicio = 'cargando...';
  bool _servicioTerminado = false;

  // ── Mapa ───────────────────────────────────────────────────────────────────
  final MapController _mapController = MapController();

  // ── HTTP ───────────────────────────────────────────────────────────────────
  final Dio _dio = Dio();

  // ── Ciclo de vida ──────────────────────────────────────────────────────────

  @override
  void initState() {
    super.initState();
    _wsService = WebSocketService();
    _inicializar();
  }

  @override
  void dispose() {
    _wsSub?.cancel();
    _wsService.dispose();
    super.dispose();
  }

  // ── Inicialización ─────────────────────────────────────────────────────────

  Future<void> _inicializar() async {
    // 1. Intentar obtener la última posición conocida del mecánico
    //    (para mostrar el marcador de inmediato sin esperar el primer ping)
    await _obtenerPosicionInicial();

    // 2. Conectar al WebSocket
    _wsService.conectar(incidenteId: widget.incidenteId);

    // 3. Escuchar mensajes
    _wsSub = _wsService.mensajes.listen(_manejarMensaje);
  }

  Future<void> _obtenerPosicionInicial() async {
    try {
      final response = await _dio.get(
        '${AppConfig.baseUrl}/ws/posicion/${widget.incidenteId}',
      );
      final posicion = response.data?['posicion'];
      if (posicion != null) {
        final lat = (posicion['lat'] as num).toDouble();
        final lng = (posicion['lng'] as num).toDouble();
        setState(() => _posicionMecanico = LatLng(lat, lng));
      }
    } on DioException catch (e) {
      // 404 = mecánico aún no envió posición — es un caso normal, no un error
      if (e.response?.statusCode != 404) {
        debugPrint('[Tracking] Error al obtener posición inicial: $e');
      }
    }
  }

  // ── Manejo de mensajes WebSocket ───────────────────────────────────────────

  void _manejarMensaje(Map<String, dynamic> msg) {
    final tipo = msg['tipo'] as String?;

    switch (tipo) {

      // Mecánico envió su posición GPS → mover marcador en el mapa
      case 'ubicacion_mecanico':
        final lat = (msg['lat'] as num?)?.toDouble();
        final lng = (msg['lng'] as num?)?.toDouble();
        if (lat != null && lng != null) {
          final nuevaPosicion = LatLng(lat, lng);
          setState(() => _posicionMecanico = nuevaPosicion);
          // Centrar el mapa en la nueva posición del mecánico
          _mapController.move(nuevaPosicion, _mapController.camera.zoom);
        }
        break;

      // Mecánico cambió el estado del servicio
      case 'cambio_estado':
        final nuevoEstado = msg['estado'] as String?;
        if (nuevoEstado != null) {
          setState(() {
            _estadoServicio = nuevoEstado;
            _servicioTerminado =
                nuevoEstado == 'finalizado' || nuevoEstado == 'cancelado';
          });

          // Mostrar notificación visual al usuario
          if (mounted) {
            _mostrarNotificacionEstado(nuevoEstado);
          }

          // Desconectar si el servicio terminó
          if (_servicioTerminado) {
            _wsService.desconectar();
          }
        }
        break;

      // Mensaje de bienvenida del servidor al conectarse
      case 'conexion_exitosa':
        // Si el servidor envía la posición en el mensaje de bienvenida, usarla
        final pos = msg['ultima_posicion_mecanico'];
        if (pos != null) {
          final lat = (pos['lat'] as num?)?.toDouble();
          final lng = (pos['lng'] as num?)?.toDouble();
          if (lat != null && lng != null) {
            setState(() => _posicionMecanico = LatLng(lat, lng));
          }
        }
        break;

      default:
        break;
    }
  }

  // ── Notificación de cambio de estado ──────────────────────────────────────

  void _mostrarNotificacionEstado(String estado) {
    final mensajes = {
      'en_camino':       '🚗 El mecánico está en camino',
      'en_atencion':     '🔧 El mecánico llegó y está atendiendo tu vehículo',
      'finalizado':      '✅ El servicio ha finalizado',
      'cancelado':       '❌ El servicio fue cancelado',
      'taller_asignado': '🏪 Se asignó un taller a tu solicitud',
    };

    final texto = mensajes[estado] ?? 'Estado actualizado: $estado';

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(texto),
        behavior: SnackBarBehavior.floating,
        backgroundColor: _colorEstado(estado),
        duration: const Duration(seconds: 4),
      ),
    );
  }

  // ── Helpers de UI ──────────────────────────────────────────────────────────

  Color _colorEstado(String estado) {
    return switch (estado) {
      'en_camino'       => Colors.blue,
      'en_atencion'     => Colors.orange,
      'finalizado'      => Colors.green,
      'cancelado'       => Colors.red,
      'taller_asignado' => Colors.purple,
      _                 => Colors.grey,
    };
  }

  String _etiquetaEstado(String estado) {
    return switch (estado) {
      'en_camino'       => 'En camino',
      'en_atencion'     => 'En atención',
      'finalizado'      => 'Finalizado',
      'cancelado'       => 'Cancelado',
      'taller_asignado' => 'Taller asignado',
      'cargando...'     => 'Cargando...',
      _                 => estado,
    };
  }

  // ── Build ──────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      appBar: AppBar(
        title: Text('Seguimiento — Incidente #${widget.incidenteId}'),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black87,
        elevation: 1,
      ),
      body: Column(
        children: [

          // ── Banner de estado en tiempo real ────────────────────────────
          _BannerEstado(
            estado: _estadoServicio,
            etiqueta: _etiquetaEstado(_estadoServicio),
            color: _colorEstado(_estadoServicio),
          ),

          // ── Mapa con marcador del mecánico ─────────────────────────────
          Expanded(
            child: _MapaTracking(
              mapController: _mapController,
              posicionMecanico: _posicionMecanico,
            ),
          ),

          // ── Panel inferior con información ─────────────────────────────
          _PanelInferior(
            posicionMecanico: _posicionMecanico,
            estadoServicio: _estadoServicio,
            servicioTerminado: _servicioTerminado,
          ),
        ],
      ),
    );
  }
}


// ─────────────────────────────────────────────────────────────────────────────
// WIDGET: Banner de estado
// ─────────────────────────────────────────────────────────────────────────────

class _BannerEstado extends StatelessWidget {
  final String estado;
  final String etiqueta;
  final Color color;

  const _BannerEstado({
    required this.estado,
    required this.etiqueta,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      color: color.withAlpha(25),
      padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 16),
      child: Row(
        children: [
          Container(
            width: 10,
            height: 10,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 8),
          Text(
            'Estado del servicio: $etiqueta',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: color.withAlpha(220),
            ),
          ),
        ],
      ),
    );
  }
}


// ─────────────────────────────────────────────────────────────────────────────
// WIDGET: Mapa de tracking
// ─────────────────────────────────────────────────────────────────────────────

class _MapaTracking extends StatelessWidget {
  final MapController mapController;
  final LatLng? posicionMecanico;

  const _MapaTracking({
    required this.mapController,
    required this.posicionMecanico,
  });

  @override
  Widget build(BuildContext context) {
    return FlutterMap(
      mapController: mapController,
      options: MapOptions(
        // Si hay posición del mecánico, centrar ahí; si no, en Santa Cruz
        initialCenter: posicionMecanico ?? const LatLng(_latInicial, _lngInicial),
        initialZoom: 14,
        interactionOptions: const InteractionOptions(
          flags: InteractiveFlag.all,
        ),
      ),
      children: [

        // ── Capa base: OpenStreetMap (gratuita, sin API key) ────────────
        TileLayer(
          urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
          userAgentPackageName: 'com.auxilio.movil',
          maxZoom: 19,
        ),

        // ── Capa de marcadores ──────────────────────────────────────────
        MarkerLayer(
          markers: [
            // Solo mostrar el marcador si el mecánico ya envió su posición
            if (posicionMecanico != null)
              Marker(
                point: posicionMecanico!,
                width: 48,
                height: 48,
                child: const _IconoMecanico(),
              ),
          ],
        ),
      ],
    );
  }
}


// ─────────────────────────────────────────────────────────────────────────────
// WIDGET: Ícono del mecánico en el mapa
// ─────────────────────────────────────────────────────────────────────────────

class _IconoMecanico extends StatelessWidget {
  const _IconoMecanico();

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.blue,
        shape: BoxShape.circle,
        border: Border.all(color: Colors.white, width: 2),
        boxShadow: const [
          BoxShadow(color: Colors.black26, blurRadius: 6, offset: Offset(0, 2))
        ],
      ),
      child: const Icon(Icons.build, color: Colors.white, size: 24),
    );
  }
}


// ─────────────────────────────────────────────────────────────────────────────
// WIDGET: Panel inferior con información del tracking
// ─────────────────────────────────────────────────────────────────────────────

class _PanelInferior extends StatelessWidget {
  final LatLng? posicionMecanico;
  final String estadoServicio;
  final bool servicioTerminado;

  const _PanelInferior({
    required this.posicionMecanico,
    required this.estadoServicio,
    required this.servicioTerminado,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      color: Colors.white,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [

          // Posición actual del mecánico (coords numéricas)
          if (posicionMecanico != null) ...[
            Row(
              children: [
                const Icon(Icons.location_on, color: Colors.blue, size: 16),
                const SizedBox(width: 4),
                Text(
                  'Mecánico: ${posicionMecanico!.latitude.toStringAsFixed(5)}, '
                  '${posicionMecanico!.longitude.toStringAsFixed(5)}',
                  style: const TextStyle(fontSize: 12, color: Colors.grey),
                ),
              ],
            ),
            const SizedBox(height: 4),
          ] else ...[
            const Row(
              children: [
                Icon(Icons.location_searching, color: Colors.grey, size: 16),
                SizedBox(width: 4),
                Text(
                  'Esperando posición del mecánico...',
                  style: TextStyle(fontSize: 12, color: Colors.grey),
                ),
              ],
            ),
            const SizedBox(height: 4),
          ],

          // Mensaje si el servicio terminó
          if (servicioTerminado)
            Container(
              width: double.infinity,
              margin: const EdgeInsets.only(top: 8),
              padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 12),
              decoration: BoxDecoration(
                color: estadoServicio == 'finalizado'
                    ? Colors.green.shade50
                    : Colors.red.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                estadoServicio == 'finalizado'
                    ? '✅ El servicio ha finalizado. Puedes calificar y pagar.'
                    : '❌ El servicio fue cancelado.',
                style: TextStyle(
                  fontSize: 13,
                  color: estadoServicio == 'finalizado'
                      ? Colors.green.shade700
                      : Colors.red.shade700,
                ),
              ),
            ),
        ],
      ),
    );
  }
}
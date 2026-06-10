// Servicio que gestiona la conexión WebSocket al endpoint del incidente.
//
// Uso:
//   final service = WebSocketService();
//   service.conectar(incidenteId: 42);
//   service.mensajes.listen((msg) { ... });
//   service.desconectar();


import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:movil/config/app_config.dart';


class WebSocketService {

  // Canal de WebSocket activo (null = no conectado)
  WebSocketChannel? _canal;

  // Controlador del stream de mensajes
  // "broadcast" permite múltiples listeners (necesario para StreamBuilder)
  final StreamController<Map<String, dynamic>> _controller =
      StreamController<Map<String, dynamic>>.broadcast();

  // ID del incidente actualmente conectado
  int? _incidenteActivo;

  // Estado público de la conexión
  bool get estaConectado => _canal != null;

  // Stream que el widget escucha para recibir mensajes
  Stream<Map<String, dynamic>> get mensajes => _controller.stream;

  /// Conecta al WebSocket del incidente indicado.
  ///
  /// [incidenteId] : ID del incidente a seguir
  /// [rol]         : 'cliente' (por defecto) o 'mecanico'
  /// [mecanicoId]  : solo si rol == 'mecanico'
  void conectar({
    required int incidenteId,
    String rol = 'cliente',
    int? mecanicoId,
  }) {
    // Si ya estamos conectados al mismo incidente, no reconectar
    if (_canal != null && _incidenteActivo == incidenteId) return;

    // Cerrar conexión anterior si existe
    desconectar();

    // Construir la URL del WebSocket con query params
    String url = '${AppConfig.wsBaseUrl}/ws/incidente/$incidenteId?rol=$rol';
    if (mecanicoId != null) url += '&mecanico_id=$mecanicoId';

    debugPrint('[WS Service] Conectando a: $url');
    _incidenteActivo = incidenteId;

    // Crear el canal (web_socket_channel se encarga del handshake)
    _canal = WebSocketChannel.connect(Uri.parse(url));

    // Suscribirse a los mensajes entrantes
    _canal!.stream.listen(
      (mensaje) {
        // Los mensajes llegan como String JSON — decodificarlos
        try {
          final data = jsonDecode(mensaje as String) as Map<String, dynamic>;
          _controller.add(data);
        } catch (e) {
          debugPrint('[WS Service] Error al decodificar mensaje: $e');
        }
      },
      onError: (error) {
        debugPrint('[WS Service] Error de WebSocket: $error');
      },
      onDone: () {
        debugPrint('[WS Service] Conexión cerrada.');
        _canal = null;
        _incidenteActivo = null;
      },
    );
  }

  /// Envía un mensaje JSON al servidor.
  void enviarMensaje(Map<String, dynamic> mensaje) {
    if (_canal != null) {
      _canal!.sink.add(jsonEncode(mensaje));
    }
  }

  /// Cierra la conexión WebSocket activa.
  /// Llamar desde dispose() del widget.
  void desconectar() {
    _canal?.sink.close();
    _canal = null;
    _incidenteActivo = null;
    debugPrint('[WS Service] Desconectado.');
  }

  /// Libera recursos del StreamController.
  /// Llamar solo cuando el objeto ya no se va a usar (destrucción definitiva).
  void dispose() {
    desconectar();
    _controller.close();
  }
}
// Encapsula toda la lógica de Firebase Messaging. Este es el servicio central del módulo. Se encarga de:
// - Inicializar Firebase
// - Pedir permisos al usuario
// - Obtener el FCM Token y enviarlo al backend
// - Configurar el handler para mensajes en foreground
// - Configurar el handler para cuando el usuario toca una notificación (background/terminated)

// movil/lib/core/services/push_notification_service.dart
//
// Servicio singleton para Firebase Cloud Messaging.
//
// Uso:
//   1. Llamar PushNotificationService.inicializar(context) en app.dart
//      después de que el usuario se autentica.
//   2. El servicio gestiona todo el resto automáticamente.
//
// Arquitectura:
//   - Las notificaciones en background/terminated las muestra el SO automáticamente.
//   - Las notificaciones en foreground las mostramos como SnackBar.
//   - Al tocar una notificación, navegamos al incidente usando GoRouter.
//
// ⚠️ IMPORTANTE: el handler de background (_firebaseMessagingBackgroundHandler)
//    debe ser una función de NIVEL SUPERIOR (fuera de cualquier clase),
//    porque Flutter la ejecuta en un isolate separado sin acceso al contexto.


import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:movil/config/app_config.dart';
import 'package:movil/core/constants/api_constants.dart';
import 'package:movil/core/network/api_client.dart';


// ─── Handler de mensajes en background ───────────────────────────────────────
// DEBE ser función de nivel superior (no un método de clase ni una función anónima).
// Flutter la ejecuta en un isolate separado cuando la app está en background.
// No tiene acceso a BuildContext, Navigator ni GoRouter.
// Solo puedes hacer operaciones sin UI (guardar en storage, logs, etc.).
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  // Si el handler usa Firebase, necesita inicializarlo también aquí
  // porque corre en un isolate separado.
  await Firebase.initializeApp();
  debugPrint('[FCM Background] Mensaje recibido: ${message.notification?.title}');
  // No podemos navegar aquí. La navegación ocurre cuando el usuario TOCA la notif.
  // Ver el listener onMessageOpenedApp más abajo.
}


class PushNotificationService {

  // Singleton: una sola instancia durante toda la vida de la app
  static final PushNotificationService _instance = PushNotificationService._internal();
  factory PushNotificationService() => _instance;
  PushNotificationService._internal();

  // Referencia al BuildContext para mostrar SnackBars en foreground.
  // Se actualiza cuando se llama a inicializar().
  BuildContext? _context;

  // Debe llamarse después de que el usuario se autentica.
  /// [context] es el BuildContext del widget raíz de la app.
  Future<void> inicializar(BuildContext context) async {
    _context = context;

    // 1. Registrar el handler de background ANTES de cualquier otra cosa
    FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);

    // 2. Pedir permisos de notificación al usuario
    await _pedirPermisos();

    // 3. Obtener el FCM token y enviarlo al backend
    await _registrarToken();

    // 4. Escuchar mensajes mientras la app está en foreground
    _configurarForeground();

    // 5. Escuchar cuando el usuario toca una notificación (app en background)
    _configurarOnMessageOpenedApp();

    // 6. Revisar si la app fue abierta por una notificación (app estaba cerrada)
    await _revisarMensajeInicial();

    debugPrint('[FCM] PushNotificationService inicializado correctamente.');
  }

  // ── Paso 1: Permisos ──────────────────────────────────────────────────────

  Future<void> _pedirPermisos() async {
    final settings = await FirebaseMessaging.instance.requestPermission(
      alert: true,      // mostrar alerta
      badge: true,      // número en el ícono de la app
      sound: true,      // sonido
      provisional: false,
    );

    debugPrint('[FCM] Estado de permisos: ${settings.authorizationStatus}');
  }

  // ── Paso 2: Token FCM ─────────────────────────────────────────────────────

  Future<void> _registrarToken() async {
    try {
      final token = await FirebaseMessaging.instance.getToken();

      if (token == null) {
        debugPrint('[FCM] No se pudo obtener el token FCM.');
        return;
      }

      debugPrint('[FCM] Token obtenido: ${token.substring(0, 20)}...');

      // Enviar el token al backend para que pueda enviar notificaciones a este dispositivo
      await ApiClient.dio.put(
        ApiConstants.pushToken,
        data: {'push_token': token},
      );

      debugPrint('[FCM] Token registrado en el backend correctamente.');
    } on DioException catch (e) {
      // Si falla el registro del token, loguear pero no romper la app
      debugPrint('[FCM] Error al registrar token en backend: ${e.message}');
    } catch (e) {
      debugPrint('[FCM] Error inesperado al registrar token: $e');
    }

    // Escuchar si el token se renueva (ej. usuario reinstala la app)
    // En ese caso, actualizamos el backend con el token nuevo
    FirebaseMessaging.instance.onTokenRefresh.listen((nuevoToken) async {
      debugPrint('[FCM] Token renovado, actualizando backend...');
      try {
        await ApiClient.dio.put(
          ApiConstants.pushToken,
          data: {'push_token': nuevoToken},
        );
      } catch (_) {}
    });
  }

  // ── Paso 3: Foreground ────────────────────────────────────────────────────

  void _configurarForeground() {
    // FirebaseMessaging.onMessage se dispara cuando la app está ABIERTA y llega un mensaje.
    // El SO Android no muestra la notificación automáticamente en este caso —
    // somos nosotros quienes decidimos cómo mostrarla.
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      debugPrint('[FCM Foreground] Mensaje recibido: ${message.notification?.title}');
      _mostrarSnackBar(message);
    });
  }

  void _mostrarSnackBar(RemoteMessage message) {
    if (_context == null || !(_context!.mounted)) return;

    final titulo = message.notification?.title ?? 'Notificación';
    final cuerpo = message.notification?.body ?? '';
    final datos = message.data;

    ScaffoldMessenger.of(_context!).showSnackBar(
      SnackBar(
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              titulo,
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            if (cuerpo.isNotEmpty)
              Text(
                cuerpo,
                style: const TextStyle(color: Colors.white70, fontSize: 12),
              ),
          ],
        ),
        backgroundColor: const Color(0xFF1e40af),   // azul del theme
        duration: const Duration(seconds: 4),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        action: datos.containsKey('incidente_id')
            ? SnackBarAction(
                label: 'Ver',
                textColor: Colors.white,
                onPressed: () => _navegarDesdeNotificacion(datos),
              )
            : null,
      ),
    );
  }


  // ── Paso 4: Tap en notif (app en background) ──────────────────────────────

  void _configurarOnMessageOpenedApp() {
    // Se dispara cuando el usuario TOCA la notificación y la app pasa de background a foreground.
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      debugPrint('[FCM] App abierta desde notificación background: ${message.data}');
      _navegarDesdeNotificacion(message.data);
    });
  }


  // ── Paso 5: App abierta desde notif (app estaba cerrada) ──────────────────

  Future<void> _revisarMensajeInicial() async {
    // getInitialMessage() retorna el mensaje que causó que la app se abriera
    // si el usuario tocó una notificación cuando la app estaba completamente cerrada.
    // Si la app se abrió normalmente, retorna null.
    final mensaje = await FirebaseMessaging.instance.getInitialMessage();

    if (mensaje != null) {
      debugPrint('[FCM] App abierta desde notificación inicial: ${mensaje.data}');
      // Pequeño delay para que el router esté listo antes de navegar
      await Future.delayed(const Duration(milliseconds: 500));
      _navegarDesdeNotificacion(mensaje.data);
    }
  }

  // ── Navegación al tocar una notificación ─────────────────────────────────

  void _navegarDesdeNotificacion(Map<String, dynamic> datos) {
    if (_context == null || !(_context!.mounted)) return;

    final tipo = datos['tipo'] as String?;
    final incidenteId = datos['incidente_id'] as String?;

    debugPrint('[FCM] Navegando desde notificación — tipo: $tipo, incidente_id: $incidenteId');

    if (incidenteId == null) return;

    // Navegar según el tipo de notificación
    switch (tipo) {
      case 'nuevo_incidente':
        // El admin del taller ve la lista de incidentes disponibles
        // (los admins usan el panel web, pero si también tienen la app, aquí irían)
        break;

      case 'estado_asignacion':
        // El cliente ve el detalle de su incidente con el estado actualizado
        _context!.pushNamed(
          'detalle-incidente',
          pathParameters: {'id': incidenteId},
        );
        break;

      default:
        // Tipo desconocido — no navegar, solo loguear
        debugPrint('[FCM] Tipo de notificación desconocido: $tipo');
    }
  }
}
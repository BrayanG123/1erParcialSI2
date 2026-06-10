// Servicio singleton que:
//   1. Escucha connectivity_plus para detectar cuando hay internet
//   2. Al detectar conexión, llama a _sincronizarPendientes()
//   3. Por cada incidente pendiente en Hive, intenta enviarlo al backend
//   4. Si el envío es exitoso → elimina de Hive
//   5. Si el servidor devuelve 409 (ya existe) → también elimina de Hive (ya fue procesado)
//   6. Si el servidor devuelve otro error → deja el incidente en Hive para reintentar


import 'dart:async';
import 'dart:io';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:movil/core/constants/api_constants.dart';
import 'package:movil/core/network/api_client.dart';
import 'package:movil/features/cliente/services/offline_incidente_service.dart';


class SincronizacionService {

  // ── Singleton ──────────────────────────────────────────────────────────────
  // Usamos el patrón singleton para que solo haya una instancia activa
  // escuchando la conectividad. Si creáramos múltiples instancias,
  // se generarían múltiples suscripciones y la sincronización se ejecutaría
  // varias veces por reconexión.
  static final SincronizacionService _instance = SincronizacionService._internal();
  factory SincronizacionService() => _instance;
  SincronizacionService._internal();

  // ── Dependencias ───────────────────────────────────────────────────────────
  final Connectivity _connectivity  = Connectivity();
  final OfflineIncidenteService _offlineService = OfflineIncidenteService();
  final Dio _dio = ApiClient.dio;

  // Suscripción al stream de conectividad
  StreamSubscription<List<ConnectivityResult>>? _sub;

  // Evitar sincronizaciones simultáneas
  bool _sincronizando = false;

   /// Inicia la escucha de conectividad.
  /// Llamar desde app.dart al arrancar la app.
  void iniciar() {
    _sub = _connectivity.onConnectivityChanged.listen(_onConectividadCambia);
    debugPrint('[Sincronizacion] Escuchando cambios de conectividad.');
  }

  /// Detiene la escucha. Llamar solo al destruir la app (raro en práctica).
  void detener() {
    _sub?.cancel();
    _sub = null;
  }

  // ── Lógica principal ───────────────────────────────────────────────────────

  void _onConectividadCambia(List<ConnectivityResult> results) {
    // ConnectivityResult puede ser una lista con múltiples tipos de conexión
    // (por ej. WiFi + VPN). Consideramos que hay conexión si al menos uno
    // no es 'none'.
    final hayConexion = results.any((r) => r != ConnectivityResult.none);

    if (hayConexion) {
      debugPrint('[Sincronizacion] Conexión detectada. Sincronizando...');
      sincronizarPendientes();
    }
  }


  /// Sincroniza todos los incidentes pendientes con el servidor.
  /// Puede ser llamado manualmente si se necesita forzar la sincronización.
  Future<void> sincronizarPendientes() async {
    // Evitar ejecución simultánea
    if (_sincronizando) return;
    _sincronizando = true;

    try {
      final pendientes = _offlineService.obtenerPendientes();

      if (pendientes.isEmpty) {
        debugPrint('[Sincronizacion] No hay incidentes pendientes.');
        return;
      }

      debugPrint('[Sincronizacion] ${pendientes.length} incidente(s) pendiente(s).');

      for (final pendiente in pendientes) {
        await _enviarIncidente(pendiente);
      }
    } finally {
      _sincronizando = false;
    }
  }


  Future<void> _enviarIncidente(IncidentePendiente pendiente) async {
    try {
      // Construir el body del incidente
      final data = <String, dynamic>{
        'descripcion':  pendiente.descripcion,
        'latitud':      pendiente.latitud,
        'longitud':     pendiente.longitud,
        'cliente_id':   pendiente.clienteId,
        if (pendiente.vehiculoId  != null) 'vehiculo_id':  pendiente.vehiculoId,
        if (pendiente.categoriaId != null) 'categoria_id': pendiente.categoriaId,
      };

      // Enviar con el idempotencyKey como header para evitar duplicados
      // (el backend puede ignorarlo si no está configurado para leerlo)
      final response = await _dio.post(
        ApiConstants.incidentes,
        data: data,
        options: Options(
          headers: {'Idempotency-Key': pendiente.idempotencyKey},
        ),
      );

      final incidenteId = response.data['id'] as int;

      // Si tiene foto/audio como archivo local, intentar subirlos
      await _subirArchivos(incidenteId, pendiente);

      // Eliminar de Hive (ya fue procesado exitosamente)
      await _offlineService.eliminar(pendiente.idempotencyKey);
      debugPrint('[Sincronizacion] Incidente ${pendiente.idempotencyKey} enviado. '
          'ID del servidor: $incidenteId');

    } on DioException catch (e) {
      final statusCode = e.response?.statusCode;

      if (statusCode == 409) {
        // 409 Conflict = el servidor ya tiene este incidente (duplicado por reintento)
        // Eliminar de Hive para no reintentar
        await _offlineService.eliminar(pendiente.idempotencyKey);
        debugPrint('[Sincronizacion] Incidente ${pendiente.idempotencyKey} '
            'ya existe en el servidor (409). Eliminado de cola.');
      } else {
        // Otro error (500, timeout, etc.) → dejar en Hive para el próximo intento
        debugPrint('[Sincronizacion] Error al enviar '
            '${pendiente.idempotencyKey}: ${e.message}. Se reintentará.');
      }
    } catch (e) {
      debugPrint('[Sincronizacion] Error inesperado: $e');
    }
  }

  /// Intenta subir foto y audio del incidente si los archivos locales existen.
  Future<void> _subirArchivos(int incidenteId, IncidentePendiente pendiente) async {
    // Subir foto si existe el archivo local
    if (pendiente.rutaFoto != null) {
      final archivo = File(pendiente.rutaFoto!);
      if (await archivo.exists()) {
        try {
          final formData = FormData.fromMap({
            'foto': await MultipartFile.fromFile(
              pendiente.rutaFoto!,
              filename: 'foto_$incidenteId.jpg',
            ),
          });
          await _dio.post(
            '${ApiConstants.incidentes}/$incidenteId/foto',
            data: formData,
          );
          debugPrint('[Sincronizacion] Foto subida para incidente $incidenteId');
        } catch (e) {
          debugPrint('[Sincronizacion] No se pudo subir foto: $e');
        }
      }
    }

    // Subir audio si existe el archivo local
    if (pendiente.rutaAudio != null) {
      final archivo = File(pendiente.rutaAudio!);
      if (await archivo.exists()) {
        try {
          final formData = FormData.fromMap({
            'audio': await MultipartFile.fromFile(
              pendiente.rutaAudio!,
              filename: 'audio_$incidenteId.m4a',
            ),
          });
          await _dio.post(
            '${ApiConstants.incidentes}/$incidenteId/audio',
            data: formData,
          );
          debugPrint('[Sincronizacion] Audio subido para incidente $incidenteId');
        } catch (e) {
          debugPrint('[Sincronizacion] No se pudo subir audio: $e');
        }
      }
    }
  }

}
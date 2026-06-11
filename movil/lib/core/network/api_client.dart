import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:movil/config/app_config.dart';
import 'package:movil/core/network/auth_interceptor.dart';

class ApiClient {
  static final Dio _dio = _crearDio();

  // Getter estático — todos los servicios usan ApiClient.dio
  static Dio get dio => _dio;

  static Dio _crearDio() {
    final dio = Dio(
      BaseOptions(
        baseUrl: AppConfig.baseUrl,
        connectTimeout: AppConfig.connectTimeout,
        receiveTimeout: AppConfig.receiveTimeout,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    // Agrega el interceptor de autenticación
    dio.interceptors.add(AuthInterceptor());

    // En modo debug, imprime cada petición y respuesta en la consola
    // Comenta estas líneas antes de subir a producción
    dio.interceptors.add(
      LogInterceptor(
        requestBody: true,
        responseBody: true,
        requestHeader: true,
        responseHeader: false,
        error: true,
        logPrint: (log) => debugPrint('[DIO] $log'),
      ),
    );

    return dio;
  }
}
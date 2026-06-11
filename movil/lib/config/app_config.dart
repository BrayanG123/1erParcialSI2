


class AppConfig {
  static const String baseUrl = 'http://192.168.0.15:8000'; // casa
  // static const String baseUrl = 'http://10.29.8.71:8000'; // Universidad
  // static const String baseUrl = 'http://192.168.43.212:8000'; // Mi celular
  // para correr en mi red
  // uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload


  // ── WebSocket (nuevo) ──────────────────────────────────────────────────
  // Mismo host que baseUrl pero con protocolo ws:// en lugar de http://
  // En producción con HTTPS, cambiar a wss://
  static const String wsBaseUrl = 'ws://192.168.0.13:8000';


  static const Duration connectTimeout = Duration(seconds: 20);
  static const Duration receiveTimeout = Duration(seconds: 35);

  static const String appName = 'AuxilioVehicular';
}
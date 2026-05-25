import 'package:flutter_secure_storage/flutter_secure_storage.dart';



class SecureStorage {

  static const _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );

  static const _keyToken = 'jwt_token';

  // Guarda el token recibido al hacer login
  static Future<void> guardarToken(String token) async {
    await _storage.write(key: _keyToken, value: token);
  }

  // Lee el token guardado. Devuelve null si no hay sesión activa.
  static Future<String?> leerToken() async {
    return await _storage.read(key: _keyToken);
  }

  // Elimina el token al cerrar sesión
  static Future<void> eliminarToken() async {
    await _storage.delete(key: _keyToken);
  }

  // Devuelve true si hay un token guardado
  static Future<bool> hayToken() async {
    final token = await _storage.read(key: _keyToken);
    return token != null && token.isNotEmpty;
  }
}
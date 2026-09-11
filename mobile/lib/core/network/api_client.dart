// mobile/lib/core/network/api_client.dart
//
// Archivo YA EXISTENTE. Se agregan saveUser(), getUser() y se actualiza
// clearToken() para que también borre los datos del usuario guardados.
// El resto del archivo (dio, interceptors, saveToken, getToken) queda igual.

import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiClient {
  // OJO: conserva tu baseUrl actual tal como la tengas configurada
  // (la IP de tu hotspot, o la que estés usando ahora). No la reemplaces
  // por este valor de ejemplo.
  static const String baseUrl = 'http://192.168.137.1:8000/api';

  late final Dio dio;
  final _storage = const FlutterSecureStorage();

  ApiClient() {
    dio = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 10),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _storage.read(key: 'access_token');
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          return handler.next(options);
        },
        onError: (error, handler) {
          return handler.next(error);
        },
      ),
    );
  }

  Future<void> saveToken(String access, String refresh) async {
    await _storage.write(key: 'access_token', value: access);
    await _storage.write(key: 'refresh_token', value: refresh);
  }

  Future<void> clearToken() async {
    await _storage.delete(key: 'access_token');
    await _storage.delete(key: 'refresh_token');
    await _storage.delete(key: 'usuario_json');
  }

  Future<String?> getToken() async {
    return await _storage.read(key: 'access_token');
  }

  /// Guarda el JSON del usuario logueado (tal como lo devuelve el login),
  /// para poder restaurar la sesión al reabrir la app sin tener que
  /// volver a pedir credenciales.
  Future<void> saveUser(String usuarioJson) async {
    await _storage.write(key: 'usuario_json', value: usuarioJson);
  }

  Future<String?> getUser() async {
    return await _storage.read(key: 'usuario_json');
  }
}

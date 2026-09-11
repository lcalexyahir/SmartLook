// mobile/lib/core/services/auth_service.dart
//
// Archivo YA EXISTENTE. Cambios:
// - login() ahora también guarda el JSON del usuario en storage seguro
//   (antes solo guardaba los tokens).
// - Se agrega intentarRestaurarSesion(), llamado al abrir la app.
// - logout() ahora usa clearToken() (que ya borra todo: tokens + usuario).
// register() y _handleError() quedan igual.

import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../network/api_client.dart';
import '../models/user_model.dart';

class AuthService extends ChangeNotifier {
  final ApiClient apiClient;

  User? _currentUser;
  bool _isLoading = false;
  String? _errorMessage;

  AuthService({required this.apiClient});

  User? get currentUser => _currentUser;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  bool get isAuthenticated => _currentUser != null;

  Future<bool> login(String correo, String password) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final response = await apiClient.dio.post(
        '/auth/login/',
        data: {
          'correo': correo,
          'password': password,
        },
      );

      final tokens = response.data['tokens'];
      await apiClient.saveToken(
        tokens['access'],
        tokens['refresh'],
      );

      // Se guarda también el usuario en storage seguro, para poder
      // restaurar la sesión al reabrir la app sin volver a pedir login.
      await apiClient.saveUser(jsonEncode(response.data['usuario']));

      _currentUser = User.fromJson(response.data['usuario']);
      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _isLoading = false;
      _errorMessage = _handleError(e);
      notifyListeners();
      return false;
    }
  }

  Future<bool> register({
    required String nombres,
    required String apellidos,
    required String correo,
    required String telefono,
    required String password,
    required String passwordConfirm,
    String? direccion,
    String? fechaNacimiento,
  }) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final response = await apiClient.dio.post(
        '/auth/registro/',
        data: {
          'nombres': nombres,
          'apellidos': apellidos,
          'correo': correo,
          'telefono': telefono,
          'password': password,
          'password_confirm': passwordConfirm,
          'direccion': direccion,
          'fecha_nacimiento': fechaNacimiento,
        },
      );

      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _isLoading = false;
      _errorMessage = _handleError(e);
      notifyListeners();
      return false;
    }
  }

  /// Se llama una sola vez, al arrancar la app (desde el SplashScreen).
  /// Si hay un token y un usuario guardados en storage seguro, restaura
  /// la sesión sin pedir login de nuevo. Devuelve true si logró restaurar.
  Future<bool> intentarRestaurarSesion() async {
    final token = await apiClient.getToken();
    if (token == null) return false;

    final usuarioJson = await apiClient.getUser();
    if (usuarioJson == null) return false;

    try {
      _currentUser = User.fromJson(jsonDecode(usuarioJson));
      notifyListeners();
      return true;
    } catch (_) {
      // Datos guardados corruptos o en formato viejo: se limpia todo
      // y se obliga a loguear de nuevo, en vez de dejar la app en un
      // estado inconsistente.
      await apiClient.clearToken();
      return false;
    }
  }

  Future<void> logout() async {
    await apiClient.clearToken();
    _currentUser = null;
    notifyListeners();
  }

  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }

  String _handleError(dynamic error) {
    if (error is DioException) {
      if (error.response?.data != null) {
        final data = error.response!.data;
        if (data is Map && data.containsKey('error')) {
          return data['error'];
        }
        if (data is Map && data.containsKey('detail')) {
          return data['detail'];
        }
      }
      return 'Error de conexión. Verifique su internet.';
    }
    return 'Error inesperado. Intente nuevamente.';
  }
}
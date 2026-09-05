import 'package:flutter/foundation.dart';
import '../network/api_client.dart';
import '../models/user_model.dart';
import 'package:dio/dio.dart';

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

    final data = response.data;

    final accessToken =
        data['tokens']?['access'] ?? data['access'];

    final refreshToken =
        data['tokens']?['refresh'] ?? data['refresh'];

    if (accessToken == null || refreshToken == null) {
      throw Exception('No se recibieron tokens JWT');
    }

    await apiClient.saveToken(
      accessToken,
      refreshToken,
    );

    final userData =
        data['usuario'] ?? data['user'];

    if (userData != null) {
      _currentUser = User.fromJson(userData);
    }

    _isLoading = false;
    notifyListeners();

    return true;

  } catch (e) {
    _isLoading = false;

    if (e is DioException) {
      final responseData = e.response?.data;

      if (responseData is Map) {
        _errorMessage =
            responseData['detail'] ??
            responseData['error'] ??
            'Error al iniciar sesión';
      } else {
        _errorMessage = 'Error al conectar con el servidor';
      }
    } else {
      _errorMessage = e.toString();
    }

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
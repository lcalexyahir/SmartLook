// mobile/lib/core/offline/conexion.dart
//
// NUEVO: utilidades compartidas para detectar falta de conexión.
import 'dart:io';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';

/// true si el teléfono tiene alguna red (wifi, datos, etc.).
bool tieneRed(List<ConnectivityResult> estado) =>
    estado.any((r) => r != ConnectivityResult.none);

/// true si el error es de red (la petición no obtuvo respuesta del servidor).
bool esErrorDeRed(Object error) {
  if (error is! DioException) return false;
  switch (error.type) {
    case DioExceptionType.connectionError:
    case DioExceptionType.connectionTimeout:
    case DioExceptionType.sendTimeout:
    case DioExceptionType.receiveTimeout:
      return true;
    case DioExceptionType.unknown:
      return error.error is SocketException || error.response == null;
    default:
      return false;
  }
}
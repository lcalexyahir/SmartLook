// mobile/lib/features/ai_assistant/services/ai_service.dart
//
// CU18/CU19: consume el asistente virtual del cliente.
//   POST /innovation/chatbot/            { mensaje }
//   GET  /innovation/chatbot/historial/
// El token JWT lo agrega el interceptor de ApiClient.
import 'package:dio/dio.dart';
import '../../../core/network/api_client.dart';

/// Prenda sugerida por el asistente (tarjeta que se muestra en el chat).
class ChatCard {
  final int idProducto;
  final String nombre;
  final String categoria;
  final double precioDesde;
  final double precioHasta;
  final List<String> tallas;
  final List<String> colores;
  final List<String> sucursales;
  final String? imagen;

  const ChatCard({
    required this.idProducto,
    required this.nombre,
    required this.categoria,
    required this.precioDesde,
    required this.precioHasta,
    required this.tallas,
    required this.colores,
    required this.sucursales,
    this.imagen,
  });

  factory ChatCard.fromJson(Map<String, dynamic> json) {
    List<String> lista(dynamic valor) =>
        valor is List ? valor.map((e) => e.toString()).toList() : <String>[];
    final imagen = json['imagen'];
    return ChatCard(
      idProducto: (json['id_producto'] as num).toInt(),
      nombre: (json['nombre'] ?? '').toString(),
      categoria: (json['categoria'] ?? '').toString(),
      precioDesde: ((json['precio_desde'] as num?) ?? 0).toDouble(),
      precioHasta: ((json['precio_hasta'] as num?) ?? 0).toDouble(),
      tallas: lista(json['tallas']),
      colores: lista(json['colores']),
      sucursales: lista(json['sucursales']),
      imagen: (imagen is String && imagen.isNotEmpty) ? imagen : null,
    );
  }

  /// Precio o rango de precios, con el mismo formato del catálogo.
  String get precio {
    final desde = 'Bs ${precioDesde.toStringAsFixed(2)}';
    if (precioDesde == precioHasta) return desde;
    return '$desde - Bs ${precioHasta.toStringAsFixed(2)}';
  }
}

/// Respuesta del asistente: texto y prendas sugeridas.
class ChatReply {
  final String respuesta;
  final List<ChatCard> tarjetas;

  const ChatReply({required this.respuesta, required this.tarjetas});

  factory ChatReply.fromJson(Map<String, dynamic> json) {
    final tarjetas = json['tarjetas'];
    return ChatReply(
      respuesta: (json['respuesta'] ?? '').toString(),
      tarjetas: tarjetas is List
          ? tarjetas
              .map((e) => ChatCard.fromJson(Map<String, dynamic>.from(e as Map)))
              .toList()
          : <ChatCard>[],
    );
  }
}

/// Un intercambio guardado (el historial no conserva las tarjetas).
class ChatHistoryItem {
  final String mensaje;
  final String respuesta;

  const ChatHistoryItem({required this.mensaje, required this.respuesta});

  factory ChatHistoryItem.fromJson(Map<String, dynamic> json) {
    return ChatHistoryItem(
      mensaje: (json['mensaje'] ?? '').toString(),
      respuesta: (json['respuesta'] ?? '').toString(),
    );
  }
}

/// Error del asistente con un mensaje listo para mostrar al cliente.
class AiServiceException implements Exception {
  final String message;

  const AiServiceException(this.message);

  @override
  String toString() => message;
}

class AiService {
  final ApiClient apiClient;

  AiService({required this.apiClient});

  /// Envía una consulta y devuelve la respuesta con sus tarjetas de prendas.
  Future<ChatReply> enviar(String mensaje) async {
    try {
      final response = await apiClient.dio.post(
        '/innovation/chatbot/',
        data: {'mensaje': mensaje},
      );
      return ChatReply.fromJson(Map<String, dynamic>.from(response.data as Map));
    } on DioException catch (e) {
      throw AiServiceException(_mensajeDeError(e));
    }
  }

  /// Últimos intercambios del cliente, del más antiguo al más nuevo.
  Future<List<ChatHistoryItem>> historial() async {
    try {
      final response = await apiClient.dio.get('/innovation/chatbot/historial/');
      final data = response.data;
      final lista = data is List ? data : <dynamic>[];
      return lista
          .map((e) => ChatHistoryItem.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } on DioException catch (e) {
      throw AiServiceException(_mensajeDeError(e));
    }
  }

  String _mensajeDeError(DioException e) {
    final estado = e.response?.statusCode;
    if (estado == 401) return 'Tu sesión expiró. Vuelve a iniciar sesión.';
    if (estado == 403) return 'El asistente es solo para clientes.';
    final data = e.response?.data;
    if (data is Map && data['detail'] is String) {
      return data['detail'] as String;
    }
    if (e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.sendTimeout ||
        e.type == DioExceptionType.receiveTimeout) {
      return 'La respuesta tardó demasiado. Intenta de nuevo en un momento.';
    }
    return 'No pude conectar con el asistente. Revisa tu conexión.';
  }
}
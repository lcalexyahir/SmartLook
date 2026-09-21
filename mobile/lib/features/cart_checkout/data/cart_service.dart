// mobile/lib/features/cart_checkout/data/cart_service.dart
import 'package:dio/dio.dart';
import '../../../core/network/api_client.dart';

class CartService {
  final ApiClient apiClient;
  CartService({required this.apiClient});

  Future<Map<String, dynamic>> getCarritoActual() async {
    final response = await apiClient.dio.get('/sales/carritos/actual/');
    return response.data as Map<String, dynamic>;
  }

  Future<void> agregarItem(int idVariante, {int cantidad = 1}) async {
    await apiClient.dio.post(
      '/sales/carrito-items/',
      data: {'id_variante': idVariante, 'cantidad': cantidad},
    );
  }

  Future<void> actualizarCantidad(int idItem, int cantidad) async {
    await apiClient.dio.patch(
      '/sales/carrito-items/$idItem/',
      data: {'cantidad': cantidad},
    );
  }

  Future<void> quitarItem(int idItem) async {
    await apiClient.dio.delete('/sales/carrito-items/$idItem/');
  }

  Future<List<dynamic>> getSucursales() async {
    final response = await apiClient.dio.get('/catalog/sucursales/');
    final data = response.data;
    return (data['results'] ?? data) as List<dynamic>;
  }

  /// CU21: cotiza el envío a domicilio del carrito actual.
  /// Devuelve {distancia_km, costo_envio, subtotal_productos, total, fuente_distancia}.
  Future<Map<String, dynamic>> cotizarEnvio({
    required int idSucursal,
    required double latitud,
    required double longitud,
  }) async {
    final response = await apiClient.dio.post(
      '/sales/carritos/cotizar-envio/',
      data: {
        'id_sucursal': idSucursal,
        'latitud': latitud,
        'longitud': longitud,
      },
    );
    return response.data as Map<String, dynamic>;
  }

  /// Paso 1: valida carrito/stock y crea el intento de pago en Stripe.
  /// Sin [entrega] es retiro en sucursal; con [entrega] es delivery
  /// ({direccion, referencia, latitud, longitud}).
  /// Devuelve {orden, client_secret}.
  Future<Map<String, dynamic>> checkout(
    int idSucursal, {
    Map<String, dynamic>? entrega,
  }) async {
    final data = <String, dynamic>{
      'id_sucursal': idSucursal,
      'tipo_entrega': entrega != null ? 'DELIVERY' : 'RETIRO',
    };
    if (entrega != null) {
      data.addAll(entrega);
    }
    final response = await apiClient.dio.post(
      '/sales/carritos/checkout/',
      data: data,
    );
    return response.data as Map<String, dynamic>;
  }

  /// Paso 2: el cliente ya confirmó la tarjeta con el SDK de Stripe.
  /// Cierra la orden en el backend (descuenta stock, etc).
  Future<Map<String, dynamic>> confirmarPago(String referenciaPago) async {
    final response = await apiClient.dio.post(
      '/sales/carritos/confirmar_pago/',
      data: {'referencia_pago': referenciaPago},
    );
    return response.data as Map<String, dynamic>;
  }

  /// CU21: dirección escrita a partir de un punto del mapa (OpenStreetMap /
  /// Nominatim). Usa un Dio aparte, sin el token de sesión, porque es un
  /// servicio externo. Si falla, devuelve null y el cliente escribe la
  /// dirección a mano.
  Future<String?> direccionDesdeCoordenadas(double lat, double lng) async {
    try {
      final response = await Dio().get(
        'https://nominatim.openstreetmap.org/reverse',
        queryParameters: {
          'format': 'jsonv2',
          'lat': lat,
          'lon': lng,
          'zoom': 18,
          'accept-language': 'es',
        },
        options: Options(
          headers: {'User-Agent': 'SmartLookMobile/1.0 (com.example.smartlook_mobile)'},
          receiveTimeout: const Duration(seconds: 10),
          sendTimeout: const Duration(seconds: 10),
        ),
      );
      final nombre = response.data['display_name'];
      if (nombre is String && nombre.isNotEmpty) {
        return nombre.length > 250 ? nombre.substring(0, 250) : nombre;
      }
      return null;
    } catch (_) {
      return null;
    }
  }
}
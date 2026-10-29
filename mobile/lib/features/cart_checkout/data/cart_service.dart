// mobile/lib/features/cart_checkout/data/cart_service.dart
//
// MODIFICADO (SaaS - A.1): el cliente tiene un carrito por tienda (empresa).
// getCarritosActivos() devuelve los carritos con prendas, cada uno con
// id_empresa y empresa_nombre. El checkout y la cotización usan la empresa
// dueña de la sucursal elegida (lo resuelve el backend).
import 'package:dio/dio.dart';
import '../../../core/network/api_client.dart';

class CartService {
  final ApiClient apiClient;
  CartService({required this.apiClient});

  /// NUEVO (SaaS): carritos activos con prendas, uno por tienda.
  Future<List<Map<String, dynamic>>> getCarritosActivos() async {
    final response = await apiClient.dio.get('/sales/carritos/activos/');
    final data = response.data;
    final lista = (data is Map ? (data['results'] ?? []) : data) as List<dynamic>;
    return lista.map((c) => Map<String, dynamic>.from(c as Map)).toList();
  }

  /// Carrito activo. Con [idEmpresa] devuelve el de esa tienda.
  Future<Map<String, dynamic>> getCarritoActual({int? idEmpresa}) async {
    final response = await apiClient.dio.get(
      '/sales/carritos/actual/',
      queryParameters: idEmpresa != null ? {'id_empresa': idEmpresa} : null,
    );
    return response.data as Map<String, dynamic>;
  }

  /// Agrega la prenda; el backend la pone en el carrito de su tienda.
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

  /// Sucursales de todas las tiendas activas; el carrito las filtra por id_empresa.
  Future<List<dynamic>> getSucursales() async {
    final response = await apiClient.dio.get('/catalog/sucursales/');
    final data = response.data;
    return (data['results'] ?? data) as List<dynamic>;
  }

  /// CU21: cotiza el envío del carrito de la tienda dueña de la sucursal.
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
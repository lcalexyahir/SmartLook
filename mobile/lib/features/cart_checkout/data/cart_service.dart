// mobile/lib/features/cart_checkout/data/cart_service.dart

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

  /// Paso 1: valida carrito/stock y crea el intento de pago en Stripe.
  /// Devuelve {orden, client_secret}.
  Future<Map<String, dynamic>> checkout(int idSucursal) async {
    final response = await apiClient.dio.post(
      '/sales/carritos/checkout/',
      data: {'id_sucursal': idSucursal},
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
}
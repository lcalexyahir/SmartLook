// mobile/lib/features/cart_checkout/data/cart_service.dart
//
// Archivo NUEVO. Consume /api/sales/carritos/actual/ y
// /api/sales/carrito-items/ (backend ya ajustado en la vuelta de web:
// CartViewSet/CartItemViewSet aislados por cliente).

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
}
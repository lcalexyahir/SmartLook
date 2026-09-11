// mobile/lib/features/admin/data/product_admin_service.dart
//
// Archivo YA EXISTENTE. Se agrega CRUD de variantes (Paso C).

import '../../../core/network/api_client.dart';

class ProductAdminService {
  final ApiClient apiClient;

  ProductAdminService({required this.apiClient});

  Future<List<dynamic>> getProductos() async {
    final response = await apiClient.dio.get('/catalog/productos/');
    final data = response.data;
    return (data['results'] ?? data) as List<dynamic>;
  }

  Future<void> crearProducto(Map<String, dynamic> datos) async {
    await apiClient.dio.post('/catalog/productos/', data: datos);
  }

  Future<void> actualizarProducto(int id, Map<String, dynamic> datos) async {
    await apiClient.dio.patch('/catalog/productos/$id/', data: datos);
  }

  Future<void> eliminarProducto(int id) async {
    await apiClient.dio.delete('/catalog/productos/$id/');
  }

  Future<void> crearVariante(Map<String, dynamic> datos) async {
    await apiClient.dio.post('/catalog/variantes/', data: datos);
  }

  Future<void> actualizarVariante(int id, Map<String, dynamic> datos) async {
    await apiClient.dio.patch('/catalog/variantes/$id/', data: datos);
  }

  Future<void> eliminarVariante(int id) async {
    await apiClient.dio.delete('/catalog/variantes/$id/');
  }
}
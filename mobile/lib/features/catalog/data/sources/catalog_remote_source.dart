import 'package:dio/dio.dart';
import '../../../../core/network/api_client.dart';

class CatalogRemoteSource {
  final ApiClient apiClient;

  CatalogRemoteSource({required this.apiClient});

  Future<Map<String, dynamic>> getProducts({
    String? categoria,
    String? marca,
    String? talla,
    String? color,
    String? busqueda,
  }) async {
    final queryParams = <String, dynamic>{};
    if (categoria != null && categoria.isNotEmpty) {
      queryParams['categoria'] = categoria;
    }
    if (marca != null && marca.isNotEmpty) {
      queryParams['marca'] = marca;
    }
    if (talla != null && talla.isNotEmpty) {
      queryParams['talla'] = talla;
    }
    if (color != null && color.isNotEmpty) {
      queryParams['color'] = color;
    }
    if (busqueda != null && busqueda.isNotEmpty) {
      queryParams['busqueda'] = busqueda;
    }

    final response = await apiClient.dio.get(
      '/catalog/productos/',
      queryParameters: queryParams,
    );
    return response.data;
  }

  Future<Map<String, dynamic>> getProduct(int id) async {
    final response = await apiClient.dio.get('/catalog/productos/$id/');
    return response.data;
  }

  Future<List<dynamic>> getCategories() async {
    final response = await apiClient.dio.get('/catalog/categorias/');
    return response.data['results'] ?? response.data;
  }

  Future<List<dynamic>> getBrands() async {
    final response = await apiClient.dio.get('/catalog/marcas/');
    return response.data['results'] ?? response.data;
  }

  Future<List<dynamic>> getSizes() async {
    final response = await apiClient.dio.get('/catalog/tallas/');
    return response.data['results'] ?? response.data;
  }

  Future<List<dynamic>> getColors() async {
    final response = await apiClient.dio.get('/catalog/colores/');
    return response.data['results'] ?? response.data;
  }

  Future<List<dynamic>> getBranches() async {
    final response = await apiClient.dio.get('/catalog/sucursales/');
    return response.data['results'] ?? response.data;
  }

  Future<List<dynamic>> getSuppliers() async {
    final response = await apiClient.dio.get('/catalog/proveedores/');
    return response.data['results'] ?? response.data;
  }
}
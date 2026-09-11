// mobile/lib/features/admin/data/attribute_service.dart
//
// Archivo YA EXISTENTE. Se agrega CRUD de Categoría, Marca, Temporada
// y Colección (CU04). Tallas/Colores quedan igual.

import '../../../core/network/api_client.dart';

class AttributeService {
  final ApiClient apiClient;

  AttributeService({required this.apiClient});

  Future<List<dynamic>> _listar(String endpoint) async {
    final response = await apiClient.dio.get(endpoint);
    final data = response.data;
    return (data['results'] ?? data) as List<dynamic>;
  }

  // ---- Tallas ----
  Future<List<dynamic>> getTallas() => _listar('/catalog/tallas/');
  Future<void> crearTalla(Map<String, dynamic> d) async { await apiClient.dio.post('/catalog/tallas/', data: d); }
  Future<void> actualizarTalla(int id, Map<String, dynamic> d) async { await apiClient.dio.patch('/catalog/tallas/$id/', data: d); }
  Future<void> eliminarTalla(int id) async { await apiClient.dio.delete('/catalog/tallas/$id/'); }

  // ---- Colores ----
  Future<List<dynamic>> getColores() => _listar('/catalog/colores/');
  Future<void> crearColor(Map<String, dynamic> d) async { await apiClient.dio.post('/catalog/colores/', data: d); }
  Future<void> actualizarColor(int id, Map<String, dynamic> d) async { await apiClient.dio.patch('/catalog/colores/$id/', data: d); }
  Future<void> eliminarColor(int id) async { await apiClient.dio.delete('/catalog/colores/$id/'); }

  // ---- Categorías ----
  Future<List<dynamic>> getCategorias() => _listar('/catalog/categorias/');
  Future<void> crearCategoria(Map<String, dynamic> d) async { await apiClient.dio.post('/catalog/categorias/', data: d); }
  Future<void> actualizarCategoria(int id, Map<String, dynamic> d) async { await apiClient.dio.patch('/catalog/categorias/$id/', data: d); }
  Future<void> eliminarCategoria(int id) async { await apiClient.dio.delete('/catalog/categorias/$id/'); }

  // ---- Marcas ----
  Future<List<dynamic>> getMarcas() => _listar('/catalog/marcas/');
  Future<void> crearMarca(Map<String, dynamic> d) async { await apiClient.dio.post('/catalog/marcas/', data: d); }
  Future<void> actualizarMarca(int id, Map<String, dynamic> d) async { await apiClient.dio.patch('/catalog/marcas/$id/', data: d); }
  Future<void> eliminarMarca(int id) async { await apiClient.dio.delete('/catalog/marcas/$id/'); }

  // ---- Temporadas ----
  Future<List<dynamic>> getTemporadas() => _listar('/catalog/temporadas/');
  Future<void> crearTemporada(Map<String, dynamic> d) async { await apiClient.dio.post('/catalog/temporadas/', data: d); }
  Future<void> actualizarTemporada(int id, Map<String, dynamic> d) async { await apiClient.dio.patch('/catalog/temporadas/$id/', data: d); }
  Future<void> eliminarTemporada(int id) async { await apiClient.dio.delete('/catalog/temporadas/$id/'); }

  // ---- Colecciones ----
  Future<List<dynamic>> getColecciones() => _listar('/catalog/colecciones/');
  Future<void> crearColeccion(Map<String, dynamic> d) async { await apiClient.dio.post('/catalog/colecciones/', data: d); }
  Future<void> actualizarColeccion(int id, Map<String, dynamic> d) async { await apiClient.dio.patch('/catalog/colecciones/$id/', data: d); }
  Future<void> eliminarColeccion(int id) async { await apiClient.dio.delete('/catalog/colecciones/$id/'); }
}
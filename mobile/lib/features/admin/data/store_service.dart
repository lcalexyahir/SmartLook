// mobile/lib/features/admin/data/store_service.dart
//
// Archivo YA EXISTENTE. Sucursales ahora tiene CRUD completo (antes
// solo lectura). Se agregan getPaises() y CRUD de ciudades. Proveedores
// queda igual.

import '../../../core/network/api_client.dart';

class StoreService {
  final ApiClient apiClient;

  StoreService({required this.apiClient});

  Future<List<dynamic>> getSucursales() async {
    final response = await apiClient.dio.get('/catalog/sucursales/');
    final data = response.data;
    return (data['results'] ?? data) as List<dynamic>;
  }

  Future<void> crearSucursal(Map<String, dynamic> datos) async {
    await apiClient.dio.post('/catalog/sucursales/', data: datos);
  }

  Future<void> actualizarSucursal(int id, Map<String, dynamic> datos) async {
    await apiClient.dio.put('/catalog/sucursales/$id/', data: datos);
  }

  Future<void> eliminarSucursal(int id) async {
    await apiClient.dio.delete('/catalog/sucursales/$id/');
  }

  Future<List<dynamic>> getPaises() async {
    final response = await apiClient.dio.get('/catalog/paises/');
    final data = response.data;
    return (data['results'] ?? data) as List<dynamic>;
  }

  Future<List<dynamic>> getCiudades() async {
    final response = await apiClient.dio.get('/catalog/ciudades/');
    final data = response.data;
    return (data['results'] ?? data) as List<dynamic>;
  }

  Future<void> crearCiudad(Map<String, dynamic> datos) async {
    await apiClient.dio.post('/catalog/ciudades/', data: datos);
  }

  Future<void> actualizarCiudad(int id, Map<String, dynamic> datos) async {
    await apiClient.dio.put('/catalog/ciudades/$id/', data: datos);
  }

  Future<void> eliminarCiudad(int id) async {
    await apiClient.dio.delete('/catalog/ciudades/$id/');
  }

  Future<List<dynamic>> getProveedores() async {
    final response = await apiClient.dio.get('/catalog/proveedores/');
    final data = response.data;
    return (data['results'] ?? data) as List<dynamic>;
  }

  Future<void> crearProveedor(Map<String, dynamic> datos) async {
    await apiClient.dio.post('/catalog/proveedores/', data: datos);
  }

  Future<void> actualizarProveedor(int id, Map<String, dynamic> datos) async {
    await apiClient.dio.patch('/catalog/proveedores/$id/', data: datos);
  }

  Future<void> eliminarProveedor(int id) async {
    await apiClient.dio.delete('/catalog/proveedores/$id/');
  }
}
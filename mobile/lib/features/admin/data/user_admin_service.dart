// mobile/lib/features/admin/data/user_admin_service.dart
//
// Archivo YA EXISTENTE. Se agrega getClientes(). El resto queda igual.

import '../../../core/network/api_client.dart';

class UserAdminService {
  final ApiClient apiClient;

  UserAdminService({required this.apiClient});

  Future<List<dynamic>> getUsuarios() async {
    final response = await apiClient.dio.get('/auth/usuarios/');
    final data = response.data;
    return (data['results'] ?? data) as List<dynamic>;
  }

  Future<List<dynamic>> getRoles() async {
    final response = await apiClient.dio.get('/auth/roles/');
    final data = response.data;
    return (data['results'] ?? data) as List<dynamic>;
  }

  Future<void> crearUsuario(Map<String, dynamic> datos) async {
    await apiClient.dio.post('/auth/usuarios/', data: datos);
  }

  Future<void> actualizarUsuario(int id, Map<String, dynamic> datos) async {
    await apiClient.dio.patch('/auth/usuarios/$id/', data: datos);
  }

  Future<void> eliminarUsuario(int id) async {
    await apiClient.dio.delete('/auth/usuarios/$id/');
  }

  Future<List<dynamic>> getPermisos() async {
    final response = await apiClient.dio.get('/auth/permisos/');
    final data = response.data;
    return (data['results'] ?? data) as List<dynamic>;
  }

  Future<List<int>> getRolPermisos(int idRol) async {
    final response = await apiClient.dio.get('/auth/roles/$idRol/permisos/');
    return List<int>.from(response.data['permisos'] ?? []);
  }

  Future<void> actualizarRolPermisos(int idRol, List<int> permisos) async {
    await apiClient.dio.put(
      '/auth/roles/$idRol/permisos/',
      data: {'permisos': permisos},
    );
  }

  Future<List<dynamic>> getBitacora() async {
    final response = await apiClient.dio.get('/auth/bitacora/');
    final data = response.data;
    return (data['results'] ?? data) as List<dynamic>;
  }

  Future<List<dynamic>> getClientes() async {
    final response = await apiClient.dio.get('/auth/usuarios/?rol=CLIENTE');
    final data = response.data;
    return (data['results'] ?? data) as List<dynamic>;
  }
}
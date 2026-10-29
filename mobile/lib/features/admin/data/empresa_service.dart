// mobile/lib/features/admin/data/empresa_service.dart
//
// NUEVO (SaaS): consulta de empresas (tenants) y sus sucursales.
// GET /auth/empresas/ (SUPER_ADMIN: todas; ADMIN_EMPRESA: la suya),
// GET /auth/empresas/<id>/ y GET /catalog/sucursales/?empresa=<slug>.
// Registrar, editar o suspender empresas se hace desde la web.
import '../../../core/network/api_client.dart';

class EmpresaService {
  final ApiClient apiClient;

  EmpresaService({required this.apiClient});

  Future<List<dynamic>> getEmpresas() async {
    final response = await apiClient.dio.get('/auth/empresas/', queryParameters: {'page_size': 100});
    final data = response.data;
    return (data is Map ? (data['results'] ?? []) : data) as List<dynamic>;
  }

  Future<Map<String, dynamic>> getEmpresa(int id) async {
    final response = await apiClient.dio.get('/auth/empresas/$id/');
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<List<dynamic>> getSucursales(String slug) async {
    final response = await apiClient.dio.get(
      '/catalog/sucursales/',
      queryParameters: {'empresa': slug, 'page_size': 100},
    );
    final data = response.data;
    return (data is Map ? (data['results'] ?? []) : data) as List<dynamic>;
  }
}
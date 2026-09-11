// mobile/lib/features/admin/data/inventory_service.dart
//
// Archivo NUEVO. Consume /api/inventory/stock/, /api/inventory/movimientos/
// y /api/inventory/movimientos/registrar/ (backend ya existente, con el
// bug de MovementCreateView corregido en views.py). También usa
// /api/catalog/sucursales/ y /api/catalog/variantes/ para llenar los
// selectores del formulario de registro.

import '../../../core/network/api_client.dart';

class InventoryService {
  final ApiClient apiClient;

  InventoryService({required this.apiClient});

  Future<List<dynamic>> getStock() async {
    final response = await apiClient.dio.get('/inventory/stock/');
    final data = response.data;
    return (data['results'] ?? data) as List<dynamic>;
  }

  Future<List<dynamic>> getMovimientos() async {
    final response = await apiClient.dio.get('/inventory/movimientos/');
    final data = response.data;
    return (data['results'] ?? data) as List<dynamic>;
  }

  Future<List<dynamic>> getSucursales() async {
    final response = await apiClient.dio.get('/catalog/sucursales/');
    final data = response.data;
    return (data['results'] ?? data) as List<dynamic>;
  }

  Future<List<dynamic>> getVariantes() async {
    final response = await apiClient.dio.get('/catalog/variantes/');
    final data = response.data;
    return (data['results'] ?? data) as List<dynamic>;
  }

  Future<void> registrarMovimiento({
    required int idSucursal,
    required int idVariante,
    required String tipoMovimiento,
    required int cantidad,
    String? motivo,
  }) async {
    await apiClient.dio.post(
      '/inventory/movimientos/registrar/',
      data: {
        'id_sucursal': idSucursal,
        'id_variante': idVariante,
        'tipo_movimiento': tipoMovimiento,
        'cantidad': cantidad,
        'motivo': motivo,
      },
    );
  }
}
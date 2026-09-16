// mobile/lib/features/admin/data/inventory_service.dart
//
// Consume /api/inventory/stock/, /api/inventory/movimientos/ y
// /api/inventory/movimientos/registrar/, además de /api/catalog/sucursales/
// y /api/catalog/variantes/ para selectores.
// NUEVO (CU16): getVariantes() acepta un parámetro opcional de búsqueda
// (código o nombre) para el mostrador de caja.

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

  Future<List<dynamic>> getVariantes({String? busqueda}) async {
    final response = await apiClient.dio.get(
      '/catalog/variantes/',
      queryParameters: busqueda != null && busqueda.isNotEmpty ? {'busqueda': busqueda} : null,
    );
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
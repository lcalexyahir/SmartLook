// mobile/lib/features/pos/data/pos_sale_service.dart

import '../../../core/network/api_client.dart';

class PosSaleService {
  final ApiClient apiClient;

  PosSaleService({required this.apiClient});

  Future<Map<String, dynamic>> registrarVenta({
    required int idSucursal,
    required String metodoPago,
    required List<Map<String, dynamic>> items,
  }) async {
    final response = await apiClient.dio.post(
      '/sales/ventas-pos/registrar/',
      data: {
        'id_sucursal': idSucursal,
        'metodo_pago': metodoPago,
        'items': items,
      },
    );
    return response.data as Map<String, dynamic>;
  }
}
// mobile/lib/features/reservations/data/reservation_service.dart
//
// Archivo NUEVO. Consume /api/reservations/reservas/ (backend ya
// existente: CU11 crear con items, CU12/CU13 listar+cancelar/confirmar/
// completar). Mismo patrón de desenvolver paginación que
// features/admin/data/inventory_service.dart.

import '../../../core/network/api_client.dart';

class ReservationService {
  final ApiClient apiClient;

  ReservationService({required this.apiClient});

  Future<Map<String, dynamic>> crearReserva({
    required int idSucursal,
    required String fechaReserva,
    required String horaReserva,
    required List<int> variantesIds,
  }) async {
    final response = await apiClient.dio.post(
      '/reservations/reservas/',
      data: {
        'id_sucursal': idSucursal,
        'fecha_reserva': fechaReserva,
        'hora_reserva': horaReserva,
        'items': variantesIds.map((id) => {'id_variante': id}).toList(),
      },
    );
    return response.data as Map<String, dynamic>;
  }

  Future<List<dynamic>> getReservas() async {
    final response = await apiClient.dio.get('/reservations/reservas/');
    final data = response.data;
    return (data['results'] ?? data) as List<dynamic>;
  }

  Future<void> cancelarReserva(int id) async {
    await apiClient.dio.post('/reservations/reservas/$id/cancelar/');
  }

  Future<void> confirmarReserva(int id) async {
    await apiClient.dio.post('/reservations/reservas/$id/confirmar/');
  }

  Future<void> completarReserva(int id) async {
    await apiClient.dio.post('/reservations/reservas/$id/completar/');
  }
}
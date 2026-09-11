// mobile/lib/features/admin/data/dashboard_service.dart
//
// Archivo NUEVO. Consume el mismo endpoint que la web:
// GET /api/bi/dashboard/

import '../../../core/network/api_client.dart';

class DashboardService {
  final ApiClient apiClient;

  DashboardService({required this.apiClient});

  Future<Map<String, dynamic>> getKpis() async {
    final response = await apiClient.dio.get('/bi/dashboard/');
    return response.data as Map<String, dynamic>;
  }
}
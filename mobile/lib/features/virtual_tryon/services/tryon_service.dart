// mobile/lib/features/virtual_tryon/services/tryon_service.dart
//
// CU17 - Vestidor Virtual (AR 2D).
//
// Servicio simple para registrar sesiones del vestidor virtual en el
// backend (bitácora que alimenta CU18/CU20 más adelante). Sigue el
// mismo patrón liviano que CartService (features/cart_checkout/data/):
// una clase con el ApiClient inyectado, sin capa de repositorio ni
// entidad separada - no hace falta para un simple registro de sesión.

import '../../../core/network/api_client.dart';


class TryonService {
  final ApiClient apiClient;

  TryonService({required this.apiClient});

  /// Registra que el cliente abrió el vestidor virtual para un
  /// producto. Es solo bitácora - quien la llama (ar_tryon_screen.dart)
  /// ignora el error si falla, porque no debe bloquear la experiencia
  /// de probarse la prenda.
  Future<void> registrarSesion(int idProducto) async {
    await apiClient.dio.post(
      '/innovation/ar-sessions/',
      data: {'id_producto': idProducto},
    );
  }
}
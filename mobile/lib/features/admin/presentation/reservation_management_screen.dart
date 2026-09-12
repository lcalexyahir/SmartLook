// mobile/lib/features/admin/presentation/reservation_management_screen.dart
//
// Archivo NUEVO. Equivalente mobile de ReservationListComponent (web)
// para el rol encargado/admin: el backend ya filtra el queryset para
// devolver TODAS las reservas con el nombre del cliente cuando el
// usuario logueado no es CLIENTE.

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/network/api_client.dart';
import '../../../shared/theme/app_colors.dart';
import '../../reservations/data/reservation_service.dart';

class ReservationManagementScreen extends StatefulWidget {
  const ReservationManagementScreen({super.key});

  @override
  State<ReservationManagementScreen> createState() => _ReservationManagementScreenState();
}

class _ReservationManagementScreenState extends State<ReservationManagementScreen> {
  late final ReservationService _reservationService;
  List<dynamic> _reservas = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    final apiClient = context.read<ApiClient>();
    _reservationService = ReservationService(apiClient: apiClient);
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() => _loading = true);
    try {
      final reservas = await _reservationService.getReservas();
      setState(() {
        _reservas = reservas;
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  Future<void> _confirmar(int id) async {
    await _reservationService.confirmarReserva(id);
    _cargar();
  }

  Future<void> _completar(int id) async {
    await _reservationService.completarReserva(id);
    _cargar();
  }

  Future<void> _cancelar(int id) async {
    try {
      await _reservationService.cancelarReserva(id);
      _cargar();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No se pudo cancelar la reserva.')),
        );
      }
    }
  }

  Color _colorEstado(String estado) {
    switch (estado) {
      case 'PENDIENTE':
        return Colors.orange;
      case 'CONFIRMADA':
        return Colors.blue;
      case 'COMPLETADA':
        return AppColors.success;
      case 'CANCELADA':
        return AppColors.danger;
      default:
        return AppColors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Reservas')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _reservas.isEmpty
              ? const Center(child: Text('No hay reservas registradas.'))
              : RefreshIndicator(
                  onRefresh: _cargar,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _reservas.length,
                    itemBuilder: (context, index) {
                      final reserva = _reservas[index];
                      final items = (reserva['items'] ?? []) as List<dynamic>;
                      final estado = reserva['estado'].toString();
                      return Card(
                        margin: const EdgeInsets.only(bottom: 12),
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          reserva['cliente']?.toString() ?? '',
                                          style: const TextStyle(fontWeight: FontWeight.w700),
                                        ),
                                        Text(
                                          reserva['sucursal']?.toString() ?? '',
                                          style: const TextStyle(color: AppColors.grey, fontSize: 12),
                                        ),
                                      ],
                                    ),
                                  ),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                    decoration: BoxDecoration(
                                      color: _colorEstado(estado).withOpacity(0.15),
                                      borderRadius: BorderRadius.circular(4),
                                    ),
                                    child: Text(
                                      estado,
                                      style: TextStyle(
                                        color: _colorEstado(estado),
                                        fontWeight: FontWeight.w600,
                                        fontSize: 12,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 6),
                              Text('${reserva['fecha_reserva']} - ${reserva['hora_reserva']}'),
                              const SizedBox(height: 6),
                              ...items.map((item) => Text('• ${item['variante']}')),
                              const SizedBox(height: 8),
                              Row(
                                mainAxisAlignment: MainAxisAlignment.end,
                                children: [
                                  if (estado == 'PENDIENTE' || estado == 'CONFIRMADA')
                                    TextButton(
                                      onPressed: () => _cancelar(reserva['id_reserva'] as int),
                                      child: const Text('Cancelar', style: TextStyle(color: AppColors.danger)),
                                    ),
                                  if (estado == 'PENDIENTE')
                                    OutlinedButton(
                                      onPressed: () => _confirmar(reserva['id_reserva'] as int),
                                      child: const Text('Confirmar'),
                                    ),
                                  if (estado == 'CONFIRMADA') ...[
                                    const SizedBox(width: 8),
                                    ElevatedButton(
                                      onPressed: () => _completar(reserva['id_reserva'] as int),
                                      child: const Text('Completar'),
                                    ),
                                  ],
                                ],
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}
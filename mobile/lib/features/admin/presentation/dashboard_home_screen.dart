// mobile/lib/features/admin/presentation/dashboard_home_screen.dart
//
// Reemplaza la versión anterior (placeholder estático). Ahora carga
// los mismos KPIs reales que la web, desde /api/bi/dashboard/.

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/network/api_client.dart';
import '../../../shared/theme/app_colors.dart';
import '../data/dashboard_service.dart';

class DashboardHomeScreen extends StatefulWidget {
  const DashboardHomeScreen({super.key});

  @override
  State<DashboardHomeScreen> createState() => _DashboardHomeScreenState();
}

class _DashboardHomeScreenState extends State<DashboardHomeScreen> {
  late final DashboardService _service;
  Map<String, dynamic>? _kpis;
  bool _cargando = true;

  @override
  void initState() {
    super.initState();
    _service = DashboardService(apiClient: context.read<ApiClient>());
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() => _cargando = true);
    try {
      final kpis = await _service.getKpis();
      setState(() {
        _kpis = kpis;
        _cargando = false;
      });
    } catch (_) {
      setState(() {
        _kpis = null;
        _cargando = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Dashboard')),
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _cargar,
              child: _kpis == null
                  ? ListView(children: const [
                      Padding(
                        padding: EdgeInsets.all(32),
                        child: Center(child: Text('No se pudieron cargar los indicadores.')),
                      )
                    ])
                  : ListView(
                      padding: const EdgeInsets.all(16),
                      children: [
                        const Text(
                          'Bienvenido a SmartLook',
                          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 4),
                        const Text(
                          'Panel principal del sistema',
                          style: TextStyle(color: Colors.grey),
                        ),
                        const SizedBox(height: 20),
                        GridView.count(
                          crossAxisCount: 2,
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          mainAxisSpacing: 12,
                          crossAxisSpacing: 12,
                          childAspectRatio: 1.3,
                          children: [
                            _TarjetaKpi(valor: '${_kpis!['total_clientes']}', etiqueta: 'Clientes registrados'),
                            _TarjetaKpi(valor: '${_kpis!['total_productos']}', etiqueta: 'Productos activos'),
                            _TarjetaKpi(valor: '${_kpis!['total_sucursales']}', etiqueta: 'Sucursales activas'),
                            _TarjetaKpi(valor: '${_kpis!['total_proveedores']}', etiqueta: 'Proveedores activos'),
                            _TarjetaKpi(valor: '${_kpis!['stock_total']}', etiqueta: 'Unidades en stock'),
                            _TarjetaKpi(valor: '${_kpis!['productos_stock_bajo']}', etiqueta: 'Variantes con stock bajo'),
                            _TarjetaKpi(valor: '${_kpis!['total_ventas_pos']}', etiqueta: 'Ventas POS'),
                            _TarjetaKpi(valor: 'Bs ${_kpis!['monto_total_ventas']}', etiqueta: 'Monto total vendido'),
                            _TarjetaKpi(valor: '${_kpis!['total_ordenes']}', etiqueta: 'Órdenes digitales'),
                            _TarjetaKpi(valor: '${_kpis!['reservas_pendientes']}', etiqueta: 'Reservas pendientes'),
                          ],
                        ),
                      ],
                    ),
            ),
    );
  }
}

class _TarjetaKpi extends StatelessWidget {
  final String valor;
  final String etiqueta;

  const _TarjetaKpi({required this.valor, required this.etiqueta});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 1,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              valor,
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
                color: AppColors.primary,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              etiqueta,
              style: const TextStyle(fontSize: 12, color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }
}
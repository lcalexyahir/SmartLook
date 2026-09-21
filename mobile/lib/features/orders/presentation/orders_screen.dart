// mobile/lib/features/orders/presentation/orders_screen.dart
//
// CU21: "Mis pedidos" del cliente. Lista sus órdenes pagadas y, si son con
// delivery, muestra la línea de tiempo del envío. Se actualiza cada 10 s.
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../../../core/network/api_client.dart';
import '../../../shared/theme/app_colors.dart';

class OrdersScreen extends StatefulWidget {
  const OrdersScreen({super.key});

  @override
  State<OrdersScreen> createState() => _OrdersScreenState();
}

class _OrdersScreenState extends State<OrdersScreen> {
  late final ApiClient _api;
  List<Map<String, dynamic>> _pedidos = [];
  bool _cargando = true;
  String? _error;
  Timer? _timer;

  static const List<String> _claves = ['PENDIENTE', 'EN_PREPARACION', 'EN_CAMINO', 'ENTREGADO'];
  static const List<String> _textos = ['Recibido', 'Preparando', 'En camino', 'Entregado'];

  @override
  void initState() {
    super.initState();
    _api = context.read<ApiClient>();
    _cargar();
    _timer = Timer.periodic(const Duration(seconds: 10), (_) => _cargar());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _cargar() async {
    try {
      final response = await _api.dio.get('/sales/ordenes/');
      final data = response.data;
      final lista = (data is Map ? (data['results'] ?? []) : data) as List;
      if (!mounted) return;
      setState(() {
        // Las órdenes PENDIENTE son pagos que nunca se completaron: no se muestran.
        _pedidos = lista
            .map((e) => Map<String, dynamic>.from(e as Map))
            .where((o) => o['estado'] != 'PENDIENTE')
            .toList();
        _cargando = false;
        _error = null;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _cargando = false;
        if (_pedidos.isEmpty) _error = 'No se pudieron cargar tus pedidos.';
      });
    }
  }

  int _indicePaso(Map<String, dynamic> o) {
    final estado = (o['delivery'] as Map?)?['estado'];
    final i = _claves.indexOf('$estado');
    return i < 0 ? 0 : i;
  }

  String _textoEstado(Map<String, dynamic> o) {
    if (o['estado'] == 'CANCELADA') return 'Cancelado';
    if (o['tipo_entrega'] == 'DELIVERY' && o['delivery'] != null) {
      return _textos[_indicePaso(o)];
    }
    return o['estado'] == 'ENTREGADA' ? 'Entregado' : 'Pagado';
  }

  Color _colorEstado(Map<String, dynamic> o) {
    if (o['estado'] == 'CANCELADA') return const Color(0xFFC62828);
    final entregado = o['estado'] == 'ENTREGADA' ||
        (o['delivery'] as Map?)?['estado'] == 'ENTREGADO';
    return entregado ? const Color(0xFF1B7F4B) : AppColors.primary;
  }

  String _fecha(dynamic iso) {
    final dt = DateTime.tryParse('$iso')?.toLocal();
    return dt == null ? '' : DateFormat('dd/MM/yyyy HH:mm').format(dt);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mis pedidos')),
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _cargar,
              child: _pedidos.isEmpty
                  ? ListView(
                      children: [
                        const SizedBox(height: 120),
                        Center(
                          child: Text(
                            _error ?? 'Todavía no tienes pedidos.',
                            style: const TextStyle(color: AppColors.grey),
                          ),
                        ),
                      ],
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: _pedidos.length,
                      itemBuilder: (context, index) => _tarjeta(_pedidos[index]),
                    ),
            ),
    );
  }

  Widget _tarjeta(Map<String, dynamic> o) {
    final delivery = o['delivery'] as Map?;
    final esDelivery = o['tipo_entrega'] == 'DELIVERY' && delivery != null;
    final items = (o['items'] ?? []) as List;
    final color = _colorEstado(o);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Pedido #${o['id_orden']}',
                          style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
                      Text(_fecha(o['fecha_creacion']),
                          style: const TextStyle(color: AppColors.grey, fontSize: 12)),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(
                    _textoEstado(o),
                    style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.w700),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            for (final i in items)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 2),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(child: Text('${i['cantidad']} x ${i['variante']}')),
                    Text('Bs ${i['subtotal']}'),
                  ],
                ),
              ),
            const Divider(height: 20),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(esDelivery ? 'Envío: Bs ${o['costo_envio']}' : ''),
                Text('Total: Bs ${o['total']}',
                    style: const TextStyle(fontWeight: FontWeight.w700)),
              ],
            ),
            if (esDelivery) ...[
              const SizedBox(height: 10),
              Text(
                'Entrega en: ${delivery['direccion']}'
                '${(delivery['referencia'] ?? '').toString().isNotEmpty ? ' (${delivery['referencia']})' : ''}',
                style: const TextStyle(fontSize: 13),
              ),
              if (delivery['repartidor'] != null) ...[
                const SizedBox(height: 2),
                Text('Repartidor: ${delivery['repartidor']}',
                    style: const TextStyle(fontSize: 13)),
              ],
              const SizedBox(height: 12),
              _lineaTiempo(_indicePaso(o)),
            ] else ...[
              const SizedBox(height: 8),
              Text('Retiro en sucursal: ${o['sucursal']}', style: const TextStyle(fontSize: 13)),
            ],
          ],
        ),
      ),
    );
  }

  Widget _lineaTiempo(int actual) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (var i = 0; i < _textos.length; i++) ...[
          if (i > 0)
            Expanded(
              child: Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Container(
                  height: 2,
                  color: i <= actual ? AppColors.primary : Colors.grey.shade300,
                ),
              ),
            ),
          Column(
            children: [
              Container(
                width: 14,
                height: 14,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: i <= actual ? AppColors.primary : Colors.grey.shade300,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                _textos[i],
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: i == actual ? FontWeight.w700 : FontWeight.w400,
                  color: i <= actual ? AppColors.primary : AppColors.grey,
                ),
              ),
            ],
          ),
        ],
      ],
    );
  }
}
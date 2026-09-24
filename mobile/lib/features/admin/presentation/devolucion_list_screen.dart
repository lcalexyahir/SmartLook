// mobile/lib/features/admin/presentation/devolucion_list_screen.dart
//
// NUEVO (devoluciones): lista de devoluciones para administración/
// encargados. Solo lectura, mismo patrón que bitacora_list_screen.dart.

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../../../core/network/api_client.dart';

class DevolucionListScreen extends StatefulWidget {
  const DevolucionListScreen({super.key});

  @override
  State<DevolucionListScreen> createState() => _DevolucionListScreenState();
}

class _DevolucionListScreenState extends State<DevolucionListScreen> {
  late final ApiClient _api;
  List<dynamic> _devoluciones = [];
  bool _cargando = true;
  final _formatoFecha = DateFormat('dd/MM/yyyy HH:mm');

  @override
  void initState() {
    super.initState();
    _api = context.read<ApiClient>();
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() => _cargando = true);
    try {
      final response = await _api.dio.get('/sales/devoluciones/');
      final data = response.data;
      final lista = (data is Map ? (data['results'] ?? []) : data) as List;
      setState(() {
        _devoluciones = lista;
        _cargando = false;
      });
    } catch (_) {
      setState(() {
        _devoluciones = [];
        _cargando = false;
      });
    }
  }

  String _formatearFecha(String? iso) {
    if (iso == null) return '';
    try {
      return _formatoFecha.format(DateTime.parse(iso).toLocal());
    } catch (_) {
      return iso;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Devoluciones')),
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _cargar,
              child: _devoluciones.isEmpty
                  ? ListView(
                      children: const [
                        Padding(
                          padding: EdgeInsets.all(32),
                          child: Center(child: Text('No hay devoluciones registradas todavía.')),
                        ),
                      ],
                    )
                  : ListView.separated(
                      itemCount: _devoluciones.length,
                      separatorBuilder: (_, __) => const Divider(height: 1),
                      itemBuilder: (context, index) {
                        final d = Map<String, dynamic>.from(_devoluciones[index] as Map);
                        final items = (d['items'] ?? []) as List;
                        return ListTile(
                          title: Text('Orden #${d['orden']} · ${d['cliente'] ?? ''}'),
                          subtitle: Text(
                            '${d['sucursal'] ?? ''}\n' +
                                items
                                    .map((i) =>
                                        '${i['cantidad']} x ${i['variante']} (${i['motivo_display']})')
                                    .join('\n'),
                          ),
                          isThreeLine: true,
                          trailing: Text(
                            _formatearFecha(d['fecha_creacion']),
                            style: const TextStyle(fontSize: 11),
                            textAlign: TextAlign.right,
                          ),
                        );
                      },
                    ),
            ),
    );
  }
}
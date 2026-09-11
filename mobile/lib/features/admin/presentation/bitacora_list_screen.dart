// mobile/lib/features/admin/presentation/bitacora_list_screen.dart
//
// Archivo NUEVO. Solo lectura. Convierte cada fecha a la hora local del
// dispositivo con .toLocal() - si el celular tiene la zona horaria de
// Bolivia bien configurada (como ya confirmamos), se ve correcta sin
// tener que hardcodear ningún offset.

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../../../core/network/api_client.dart';
import '../data/user_admin_service.dart';

class BitacoraListScreen extends StatefulWidget {
  const BitacoraListScreen({super.key});

  @override
  State<BitacoraListScreen> createState() => _BitacoraListScreenState();
}

class _BitacoraListScreenState extends State<BitacoraListScreen> {
  late final UserAdminService _service;
  List<dynamic> _eventos = [];
  bool _cargando = true;
  final _formatoFecha = DateFormat('dd/MM/yyyy HH:mm:ss');

  @override
  void initState() {
    super.initState();
    _service = UserAdminService(apiClient: context.read<ApiClient>());
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() => _cargando = true);
    try {
      final eventos = await _service.getBitacora();
      setState(() {
        _eventos = eventos;
        _cargando = false;
      });
    } catch (_) {
      setState(() {
        _eventos = [];
        _cargando = false;
      });
    }
  }

  String _formatearFecha(String? iso) {
    if (iso == null) return '';
    try {
      final fecha = DateTime.parse(iso).toLocal();
      return _formatoFecha.format(fecha);
    } catch (_) {
      return iso;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Bitácora del Sistema')),
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _cargar,
              child: _eventos.isEmpty
                  ? ListView(
                      children: const [
                        Padding(
                          padding: EdgeInsets.all(32),
                          child: Center(child: Text('No hay eventos registrados.')),
                        ),
                      ],
                    )
                  : ListView.separated(
                      itemCount: _eventos.length,
                      separatorBuilder: (_, __) => const Divider(height: 1),
                      itemBuilder: (context, index) {
                        final evento = _eventos[index];
                        return ListTile(
                          title: Text(evento['accion'] ?? ''),
                          subtitle: Text(
                            '${evento['usuario'] ?? 'Sistema / Anónimo'} · '
                            '${evento['tabla_afectada'] ?? ''}\n'
                            '${evento['descripcion'] ?? ''}\n'
                            'IP: ${evento['direccion_ip'] ?? 'N/A'}',
                          ),
                          isThreeLine: true,
                          trailing: Text(
                            _formatearFecha(evento['fecha_evento']),
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
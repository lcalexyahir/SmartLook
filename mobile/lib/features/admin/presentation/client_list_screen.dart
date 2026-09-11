// mobile/lib/features/admin/presentation/client_list_screen.dart
//
// Archivo NUEVO. Solo lectura: el admin no crea clientes (se registran
// ellos mismos, CU01).

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../../../core/network/api_client.dart';
import '../data/user_admin_service.dart';

class ClientListScreen extends StatefulWidget {
  const ClientListScreen({super.key});

  @override
  State<ClientListScreen> createState() => _ClientListScreenState();
}

class _ClientListScreenState extends State<ClientListScreen> {
  late final UserAdminService _service;
  List<dynamic> _clientes = [];
  bool _cargando = true;
  String _busqueda = '';
  final _formatoFecha = DateFormat('dd/MM/yyyy HH:mm');

  @override
  void initState() {
    super.initState();
    _service = UserAdminService(apiClient: context.read<ApiClient>());
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() => _cargando = true);
    try {
      final clientes = await _service.getClientes();
      setState(() {
        _clientes = clientes;
        _cargando = false;
      });
    } catch (_) {
      setState(() {
        _clientes = [];
        _cargando = false;
      });
    }
  }

  List<dynamic> get _clientesFiltrados {
    if (_busqueda.isEmpty) return _clientes;
    final termino = _busqueda.toLowerCase();
    return _clientes.where((c) {
      final nombre = '${c['nombres']} ${c['apellidos']}'.toLowerCase();
      final correo = (c['correo'] ?? '').toString().toLowerCase();
      return nombre.contains(termino) || correo.contains(termino);
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Clientes')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              decoration: const InputDecoration(
                hintText: 'Buscar por nombre o correo...',
                prefixIcon: Icon(Icons.search),
                border: OutlineInputBorder(),
              ),
              onChanged: (v) => setState(() => _busqueda = v),
            ),
          ),
          Expanded(
            child: _cargando
                ? const Center(child: CircularProgressIndicator())
                : RefreshIndicator(
                    onRefresh: _cargar,
                    child: _clientesFiltrados.isEmpty
                        ? ListView(
                            children: const [
                              Padding(
                                padding: EdgeInsets.all(32),
                                child: Center(child: Text('No hay clientes registrados todavía.')),
                              ),
                            ],
                          )
                        : ListView.separated(
                            itemCount: _clientesFiltrados.length,
                            separatorBuilder: (_, __) => const Divider(height: 1),
                            itemBuilder: (context, index) {
                              final cliente = _clientesFiltrados[index];
                              String registrado = '';
                              try {
                                registrado = _formatoFecha.format(
                                  DateTime.parse(cliente['fecha_creacion']).toLocal(),
                                );
                              } catch (_) {}

                              return ListTile(
                                title: Text('${cliente['nombres']} ${cliente['apellidos']}'),
                                subtitle: Text(
                                  '${cliente['correo']}\n'
                                  'Tel: ${cliente['telefono'] ?? 'N/A'} · Registrado: $registrado',
                                ),
                                isThreeLine: true,
                                trailing: Chip(
                                  label: Text(
                                    cliente['estado'] ?? '',
                                    style: const TextStyle(fontSize: 11),
                                  ),
                                  backgroundColor: cliente['estado'] == 'ACTIVO'
                                      ? Colors.green.shade50
                                      : Colors.grey.shade200,
                                ),
                              );
                            },
                          ),
                  ),
          ),
        ],
      ),
    );
  }
}
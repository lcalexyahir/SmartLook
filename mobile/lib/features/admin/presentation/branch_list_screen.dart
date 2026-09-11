// mobile/lib/features/admin/presentation/branch_list_screen.dart
//
// Archivo NUEVO. Solo lectura: SucursalViewSet en el backend es
// ReadOnlyModelViewSet (aún no permite crear/editar sucursales por API,
// ni en mobile ni en la web realmente).

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/network/api_client.dart';
import '../data/store_service.dart';

class BranchListScreen extends StatefulWidget {
  const BranchListScreen({super.key});

  @override
  State<BranchListScreen> createState() => _BranchListScreenState();
}

class _BranchListScreenState extends State<BranchListScreen> {
  late final StoreService _service;
  List<dynamic> _sucursales = [];
  bool _cargando = true;

  @override
  void initState() {
    super.initState();
    _service = StoreService(apiClient: context.read<ApiClient>());
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() => _cargando = true);
    try {
      final sucursales = await _service.getSucursales();
      setState(() {
        _sucursales = sucursales;
        _cargando = false;
      });
    } catch (_) {
      setState(() {
        _sucursales = [];
        _cargando = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Sucursales')),
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _cargar,
              child: _sucursales.isEmpty
                  ? ListView(children: const [
                      Padding(
                        padding: EdgeInsets.all(32),
                        child: Center(child: Text('No hay sucursales registradas.')),
                      )
                    ])
                  : ListView.separated(
                      itemCount: _sucursales.length,
                      separatorBuilder: (_, __) => const Divider(height: 1),
                      itemBuilder: (context, index) {
                        final sucursal = _sucursales[index];
                        final ciudad = sucursal['ciudad']?['nombre'] ?? '';
                        final pais = sucursal['ciudad']?['pais']?['nombre'] ?? '';

                        return ListTile(
                          title: Text(sucursal['nombre'] ?? ''),
                          subtitle: Text(
                            '${sucursal['direccion'] ?? ''}\n'
                            '$ciudad, $pais · Tel: ${sucursal['telefono'] ?? 'N/A'}',
                          ),
                          isThreeLine: true,
                          trailing: Chip(
                            label: Text(
                              sucursal['estado'] ?? '',
                              style: const TextStyle(fontSize: 11),
                            ),
                            backgroundColor: sucursal['estado'] == 'ACTIVA'
                                ? Colors.green.shade50
                                : Colors.grey.shade200,
                          ),
                        );
                      },
                    ),
            ),
    );
  }
}
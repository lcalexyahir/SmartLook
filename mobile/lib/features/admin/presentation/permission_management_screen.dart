// mobile/lib/features/admin/presentation/permission_management_screen.dart
//
// Archivo NUEVO. Selector de rol (incluye CLIENTE, a diferencia de
// Usuarios y Roles) + checklist de permisos con guardar.

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/network/api_client.dart';
import '../data/user_admin_service.dart';

class PermissionManagementScreen extends StatefulWidget {
  const PermissionManagementScreen({super.key});

  @override
  State<PermissionManagementScreen> createState() => _PermissionManagementScreenState();
}

class _PermissionManagementScreenState extends State<PermissionManagementScreen> {
  late final UserAdminService _service;
  List<dynamic> _roles = [];
  List<dynamic> _permisos = [];
  int? _rolSeleccionado;
  Set<int> _idsAsignados = {};
  bool _cargandoInicial = true;
  bool _cargandoPermisosRol = false;
  bool _guardando = false;
  String? _mensaje;
  bool _esError = false;

  @override
  void initState() {
    super.initState();
    _service = UserAdminService(apiClient: context.read<ApiClient>());
    _cargarInicial();
  }

  Future<void> _cargarInicial() async {
    try {
      final roles = await _service.getRoles();
      final permisos = await _service.getPermisos();
      setState(() {
        _roles = roles;
        _permisos = permisos;
        _cargandoInicial = false;
      });
    } catch (_) {
      setState(() => _cargandoInicial = false);
    }
  }

  Future<void> _seleccionarRol(int idRol) async {
    setState(() {
      _rolSeleccionado = idRol;
      _cargandoPermisosRol = true;
      _mensaje = null;
    });

    try {
      final ids = await _service.getRolPermisos(idRol);
      setState(() {
        _idsAsignados = ids.toSet();
        _cargandoPermisosRol = false;
      });
    } catch (_) {
      setState(() {
        _idsAsignados = {};
        _cargandoPermisosRol = false;
      });
    }
  }

  Future<void> _guardar() async {
    if (_rolSeleccionado == null) return;

    setState(() {
      _guardando = true;
      _mensaje = null;
    });

    try {
      await _service.actualizarRolPermisos(
        _rolSeleccionado!,
        _idsAsignados.toList(),
      );
      setState(() {
        _guardando = false;
        _mensaje = 'Permisos actualizados correctamente.';
        _esError = false;
      });
    } catch (_) {
      setState(() {
        _guardando = false;
        _mensaje = 'No se pudieron guardar los permisos.';
        _esError = true;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Permisos')),
      body: _cargandoInicial
          ? const Center(child: CircularProgressIndicator())
          : Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  DropdownButtonFormField<int>(
                    value: _rolSeleccionado,
                    decoration: const InputDecoration(labelText: 'Seleccione un rol'),
                    items: _roles.map<DropdownMenuItem<int>>((rol) {
                      return DropdownMenuItem(
                        value: rol['id_rol'] as int,
                        child: Text(rol['nombre']),
                      );
                    }).toList(),
                    onChanged: (v) {
                      if (v != null) _seleccionarRol(v);
                    },
                  ),
                  const SizedBox(height: 12),
                  if (_mensaje != null)
                    Text(
                      _mensaje!,
                      style: TextStyle(color: _esError ? Colors.red : Colors.green),
                    ),
                  if (_rolSeleccionado != null && _cargandoPermisosRol)
                    const Expanded(
                      child: Center(child: CircularProgressIndicator()),
                    ),
                  if (_rolSeleccionado != null && !_cargandoPermisosRol) ...[
                    Expanded(
                      child: _permisos.isEmpty
                          ? const Center(child: Text('No hay permisos en el catálogo.'))
                          : ListView.builder(
                              itemCount: _permisos.length,
                              itemBuilder: (context, index) {
                                final permiso = _permisos[index];
                                final id = permiso['id_permiso'] as int;
                                return CheckboxListTile(
                                  value: _idsAsignados.contains(id),
                                  title: Text(permiso['nombre'] ?? ''),
                                  subtitle: (permiso['descripcion'] ?? '').toString().isNotEmpty
                                      ? Text(permiso['descripcion'])
                                      : null,
                                  onChanged: (marcado) {
                                    setState(() {
                                      if (marcado == true) {
                                        _idsAsignados.add(id);
                                      } else {
                                        _idsAsignados.remove(id);
                                      }
                                    });
                                  },
                                );
                              },
                            ),
                    ),
                    const SizedBox(height: 8),
                    ElevatedButton(
                      onPressed: _guardando ? null : _guardar,
                      child: Text(_guardando ? 'Guardando...' : 'Guardar Permisos'),
                    ),
                  ],
                ],
              ),
            ),
    );
  }
}
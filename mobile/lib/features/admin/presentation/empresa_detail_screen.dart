// mobile/lib/features/admin/presentation/empresa_detail_screen.dart
//
// NUEVO (SaaS): detalle de una empresa (igual que la web, solo consulta):
// logo, estado, datos, administrador, suscripción y sus sucursales.
// El SUPER_ADMIN llega desde la lista; el ADMIN_EMPRESA, directo a la suya.
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/network/api_client.dart';
import '../../../shared/theme/app_colors.dart';
import '../data/empresa_service.dart';
import 'empresa_list_screen.dart' show formatoFecha;
import 'empresa_logo.dart';

class EmpresaDetailScreen extends StatefulWidget {
  final int idEmpresa;

  const EmpresaDetailScreen({super.key, required this.idEmpresa});

  @override
  State<EmpresaDetailScreen> createState() => _EmpresaDetailScreenState();
}

class _EmpresaDetailScreenState extends State<EmpresaDetailScreen> {
  late final EmpresaService _service;
  Map<String, dynamic>? _empresa;
  List<dynamic> _sucursales = [];
  bool _cargando = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _service = EmpresaService(apiClient: context.read<ApiClient>());
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      final empresa = await _service.getEmpresa(widget.idEmpresa);
      List<dynamic> sucursales = [];
      final slug = empresa['slug']?.toString();
      if (slug != null && slug.isNotEmpty) {
        try {
          sucursales = await _service.getSucursales(slug);
        } catch (_) {
          sucursales = [];
        }
      }
      if (!mounted) return;
      setState(() {
        _empresa = empresa;
        _sucursales = sucursales;
        _cargando = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _cargando = false;
        _error = 'No se pudo cargar la empresa.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final e = _empresa;
    return Scaffold(
      appBar: AppBar(title: Text(e?['nombre']?.toString() ?? 'Empresa')),
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : e == null
              ? Center(child: Text(_error ?? 'No se pudo cargar la empresa.',
                  style: const TextStyle(color: AppColors.danger)))
              : RefreshIndicator(
                  onRefresh: _cargar,
                  child: ListView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(16),
                    children: [
                      _perfil(e),
                      _seccion('Datos', [
                        _fila('NIT', e['nit']),
                        _fila('Correo', e['correo_contacto']),
                        _fila('Teléfono', e['telefono']),
                      ]),
                      _seccion(
                        'Administrador',
                        e['administrador'] is Map
                            ? [
                                _fila('Nombre', e['administrador']['nombre']),
                                _fila('Correo', e['administrador']['correo']),
                                _fila('Teléfono', e['administrador']['telefono']),
                              ]
                            : [const Text('Sin administrador asignado.',
                                style: TextStyle(color: AppColors.grey))],
                      ),
                      _seccionSuscripcion(e['suscripcion'] is Map ? e['suscripcion'] as Map : null),
                      _seccionSucursales(),
                    ],
                  ),
                ),
    );
  }

  Widget _perfil(Map<String, dynamic> e) {
    final activa = e['estado'] == 'ACTIVA';
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            EmpresaLogo(logo: e['logo'] as String?, nombre: '${e['nombre'] ?? ''}', tamano: 72),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('${e['nombre'] ?? ''}',
                      style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 6),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: (activa ? AppColors.success : AppColors.danger).withOpacity(0.15),
                      borderRadius: BorderRadius.circular(999),
                    ),
                    child: Text(
                      '${e['estado'] ?? ''}',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                        color: activa ? AppColors.success : AppColors.danger,
                      ),
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text('Registrada el ${formatoFecha(e['fecha_creacion'])}',
                      style: const TextStyle(fontSize: 12, color: AppColors.grey)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _seccion(String titulo, List<Widget> hijos) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(titulo, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            ...hijos,
          ],
        ),
      ),
    );
  }

  Widget _fila(String etiqueta, dynamic valor, {Color? color}) {
    final texto = (valor == null || '$valor'.isEmpty) ? '-' : '$valor';
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(etiqueta, style: const TextStyle(color: AppColors.grey)),
          ),
          Expanded(
            child: Text(texto, style: TextStyle(fontWeight: FontWeight.w600, color: color)),
          ),
        ],
      ),
    );
  }

  Widget _seccionSuscripcion(Map? s) {
    if (s == null) {
      return _seccion('Suscripción', [
        const Text('Sin suscripción.', style: TextStyle(color: AppColors.grey)),
      ]);
    }
    final dias = int.tryParse('${s['dias_restantes']}');
    return _seccion('Suscripción', [
      _fila('Plan', s['plan_nombre']),
      _fila('Inicio', formatoFecha(s['fecha_inicio'])),
      _fila('Vencimiento', formatoFecha(s['fecha_vencimiento'])),
      _fila(
        'Tiempo restante',
        dias == null ? '-' : (dias < 0 ? 'Vencida' : '$dias días'),
        color: (dias != null && dias <= 7) ? AppColors.danger : null,
      ),
      _fila('Estado', s['estado']),
    ]);
  }

  Widget _seccionSucursales() {
    return _seccion('Sucursales (${_sucursales.length})', [
      if (_sucursales.isEmpty)
        const Text('La empresa todavía no tiene sucursales.',
            style: TextStyle(color: AppColors.grey))
      else
        ..._sucursales.map((s) {
          final activa = s['estado'] == 'ACTIVA';
          final ciudad = s['ciudad'] is Map ? s['ciudad']['nombre'] : null;
          return Container(
            padding: const EdgeInsets.symmetric(vertical: 10),
            decoration: const BoxDecoration(
              border: Border(top: BorderSide(color: Color(0xFFEEEEEE))),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text('${s['nombre'] ?? ''}',
                          style: const TextStyle(fontWeight: FontWeight.bold)),
                    ),
                    Text(
                      '${s['estado'] ?? ''}',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                        color: activa ? AppColors.success : AppColors.danger,
                      ),
                    ),
                  ],
                ),
                if (ciudad != null)
                  Text('$ciudad', style: const TextStyle(fontSize: 13, color: AppColors.grey)),
                Text('${s['direccion'] ?? ''}', style: const TextStyle(fontSize: 13)),
                if ((s['telefono'] ?? '').toString().isNotEmpty)
                  Text('Tel. ${s['telefono']}',
                      style: const TextStyle(fontSize: 13, color: AppColors.grey)),
              ],
            ),
          );
        }),
    ]);
  }
}
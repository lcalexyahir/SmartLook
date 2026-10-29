// mobile/lib/features/admin/presentation/empresa_list_screen.dart
//
// NUEVO (SaaS): lista de empresas para el SUPER_ADMIN, con su logo, estado,
// plan, vencimiento de la suscripción y cantidad de sucursales (igual que la
// web). Solo consulta: registrar o suspender empresas se hace desde la web.
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/network/api_client.dart';
import '../../../shared/theme/app_colors.dart';
import '../data/empresa_service.dart';
import 'empresa_detail_screen.dart';
import 'empresa_logo.dart';

class EmpresaListScreen extends StatefulWidget {
  const EmpresaListScreen({super.key});

  @override
  State<EmpresaListScreen> createState() => _EmpresaListScreenState();
}

class _EmpresaListScreenState extends State<EmpresaListScreen> {
  late final EmpresaService _service;
  List<dynamic> _empresas = [];
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
      final empresas = await _service.getEmpresas();
      if (!mounted) return;
      setState(() {
        _empresas = empresas;
        _cargando = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _cargando = false;
        _error = 'No se pudieron cargar las empresas.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Empresas')),
      body: RefreshIndicator(
        onRefresh: _cargar,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          children: [
            if (_cargando)
              const Padding(
                padding: EdgeInsets.all(24),
                child: Center(child: CircularProgressIndicator()),
              )
            else if (_error != null)
              Text(_error!, style: const TextStyle(color: AppColors.danger))
            else if (_empresas.isEmpty)
              const Padding(
                padding: EdgeInsets.all(24),
                child: Center(child: Text('No hay empresas registradas.')),
              )
            else
              ..._empresas.map((e) => _tarjeta(Map<String, dynamic>.from(e as Map))),
          ],
        ),
      ),
    );
  }

  Widget _tarjeta(Map<String, dynamic> e) {
    final activa = e['estado'] == 'ACTIVA';
    final s = e['suscripcion'] is Map ? e['suscripcion'] as Map : null;
    final dias = int.tryParse('${s?['dias_restantes']}');
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => EmpresaDetailScreen(idEmpresa: e['id_empresa'] as int),
          ),
        ).then((_) => _cargar()),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              EmpresaLogo(logo: e['logo'] as String?, nombre: '${e['nombre'] ?? ''}'),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            '${e['nombre'] ?? ''}',
                            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                          ),
                        ),
                        _badgeEstado('${e['estado'] ?? ''}', activa),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Plan ${s?['plan_nombre'] ?? '-'} · ${e['total_sucursales'] ?? 0} sucursal(es)',
                      style: const TextStyle(fontSize: 13, color: AppColors.grey),
                    ),
                    const SizedBox(height: 2),
                    if (s != null)
                      Text(
                        '${(dias ?? 0) < 0 ? 'Venció' : 'Vence'} el ${formatoFecha(s['fecha_vencimiento'])}'
                        '${(dias ?? -1) >= 0 ? ' ($dias días)' : ''}',
                        style: TextStyle(
                          fontSize: 13,
                          color: (dias != null && dias <= 7) ? AppColors.danger : AppColors.grey,
                          fontWeight: (dias != null && dias <= 7) ? FontWeight.w600 : FontWeight.normal,
                        ),
                      )
                    else
                      const Text('Sin suscripción',
                          style: TextStyle(fontSize: 13, color: AppColors.danger)),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: AppColors.grey),
            ],
          ),
        ),
      ),
    );
  }
}

/// Fecha "2026-11-30" -> "30/11/2026".
String formatoFecha(dynamic valor) {
  final fecha = DateTime.tryParse('${valor ?? ''}');
  if (fecha == null) return '-';
  return '${fecha.day.toString().padLeft(2, '0')}/${fecha.month.toString().padLeft(2, '0')}/${fecha.year}';
}

Widget _badgeEstado(String estado, bool activa) {
  return Container(
    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
    decoration: BoxDecoration(
      color: (activa ? AppColors.success : AppColors.danger).withOpacity(0.15),
      borderRadius: BorderRadius.circular(999),
    ),
    child: Text(
      estado,
      style: TextStyle(
        fontSize: 11,
        fontWeight: FontWeight.bold,
        color: activa ? AppColors.success : AppColors.danger,
      ),
    ),
  );
}
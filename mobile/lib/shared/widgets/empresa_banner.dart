// mobile/lib/shared/widgets/empresa_banner.dart
//
// NUEVO (SaaS - A.2): empresa y sucursal del personal, con su plan y el
// tiempo restante de la suscripción (solo consulta; se paga en la web).
// No muestra nada para SUPER_ADMIN ni clientes (no pertenecen a una empresa).
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../../core/network/api_client.dart';
import '../../core/services/auth_service.dart';
import '../theme/app_colors.dart';

class EmpresaBanner extends StatefulWidget {
  const EmpresaBanner({super.key});

  @override
  State<EmpresaBanner> createState() => _EmpresaBannerState();
}

class _EmpresaBannerState extends State<EmpresaBanner> {
  Map<String, dynamic>? _suscripcion;

  @override
  void initState() {
    super.initState();
    final usuario = context.read<AuthService>().currentUser;
    if (usuario?.idEmpresa != null) _cargarSuscripcion();
  }

  Future<void> _cargarSuscripcion() async {
    try {
      final response =
          await context.read<ApiClient>().dio.get('/auth/suscripciones/actual/');
      if (!mounted) return;
      setState(() => _suscripcion = Map<String, dynamic>.from(response.data as Map));
    } catch (_) {
      // Sin suscripción o sin conexión: solo se muestra la empresa.
    }
  }

  String _textoPlan(Map<String, dynamic> s) {
    final plan = (s['plan'] is Map) ? (s['plan']['nombre']?.toString() ?? '') : '';
    final dias = int.tryParse('${s['dias_restantes']}');
    final fecha = DateTime.tryParse('${s['fecha_vencimiento'] ?? ''}');
    final fechaTexto = fecha == null ? '' : DateFormat('dd/MM/yyyy').format(fecha);
    final partes = <String>[if (plan.isNotEmpty) 'Plan $plan'];
    if (dias != null && dias < 0) {
      partes.add(fechaTexto.isEmpty ? 'Vencida' : 'Venció el $fechaTexto');
    } else if (fechaTexto.isNotEmpty) {
      partes.add('Vence el $fechaTexto${dias != null ? ' ($dias días)' : ''}');
    }
    return partes.join(' · ');
  }

  @override
  Widget build(BuildContext context) {
    final usuario = context.watch<AuthService>().currentUser;
    final empresa = usuario?.empresaNombre ?? '';
    if (usuario == null || empresa.isEmpty) return const SizedBox.shrink();
    final sucursal = usuario.sucursalCorta;
    final dias = int.tryParse('${_suscripcion?['dias_restantes']}');
    final alerta = dias != null && dias <= 7;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
          decoration: BoxDecoration(
            color: AppColors.primary.withOpacity(0.12),
            borderRadius: BorderRadius.circular(999),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.storefront_outlined, size: 16, color: AppColors.accent),
              const SizedBox(width: 6),
              Flexible(
                child: Text(
                  sucursal != null ? '$empresa · $sucursal' : empresa,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textDark,
                  ),
                ),
              ),
            ],
          ),
        ),
        if (_suscripcion != null) ...[
          const SizedBox(height: 6),
          Text(
            _textoPlan(_suscripcion!),
            style: TextStyle(
              fontSize: 12,
              fontWeight: alerta ? FontWeight.w700 : FontWeight.w500,
              color: alerta ? AppColors.danger : AppColors.grey,
            ),
          ),
        ],
      ],
    );
  }
}
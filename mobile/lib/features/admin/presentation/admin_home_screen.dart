// mobile/lib/features/admin/presentation/admin_home_screen.dart
//
// MODIFICADO (CU12): se agrega la tarjeta "Reservas", que navega a
// ReservationManagementScreen (el encargado ve todas las reservas con
// el nombre del cliente, y puede confirmar/completar/cancelar).

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../../../core/services/auth_service.dart';
import '../../../shared/theme/app_colors.dart';
import 'user_management_screen.dart';
import 'permission_management_screen.dart';
import 'bitacora_list_screen.dart';
import 'client_list_screen.dart';
import 'inventory_screen.dart';
import 'branch_management_screen.dart';
import 'supplier_management_screen.dart';
import 'dashboard_home_screen.dart';
import 'attribute_management_screen.dart';
import 'product_management_screen.dart';
import 'reservation_management_screen.dart';

class AdminHomeScreen extends StatelessWidget {
  const AdminHomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final authService = context.watch<AuthService>();
    final usuario = authService.currentUser;

    final secciones = <_SeccionAdmin>[
      _SeccionAdmin('Dashboard', Icons.dashboard_outlined, 'dashboard'),
      _SeccionAdmin('Usuarios y Roles', Icons.people_outline, 'usuarios'),
      _SeccionAdmin('Productos', Icons.checkroom_outlined, 'productos'),
      _SeccionAdmin('Atributos de Producto', Icons.straighten_outlined, 'atributos'),
      _SeccionAdmin('Permisos', Icons.lock_outline, 'permisos'),
      _SeccionAdmin('Inventario', Icons.inventory_2_outlined, 'inventario'),
      _SeccionAdmin('Reservas', Icons.event_available_outlined, 'reservas'),
      _SeccionAdmin('Sucursales', Icons.storefront_outlined, 'sucursales'),
      _SeccionAdmin('Proveedores', Icons.local_shipping_outlined, 'proveedores'),
      _SeccionAdmin('Clientes', Icons.person_outline, 'clientes'),
      _SeccionAdmin('Bitácora', Icons.receipt_long_outlined, 'bitacora'),
    ];

    return Scaffold(
      backgroundColor: AppColors.panelBg,
      appBar: AppBar(
        backgroundColor: AppColors.bgDeep,
        elevation: 0,
        title: Text(
          'SmartLook',
          style: GoogleFonts.fraunces(
            fontSize: 18,
            fontWeight: FontWeight.w500,
            color: AppColors.panelBg,
          ),
        ),
        iconTheme: const IconThemeData(color: AppColors.panelBg),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Cerrar sesión',
            onPressed: () async {
              await authService.logout();
              if (context.mounted) {
                Navigator.pushReplacementNamed(context, '/login');
              }
            },
          ),
        ],
      ),
      body: Column(
        children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.white,
              border: Border(
                bottom: BorderSide(color: AppColors.line),
                top: const BorderSide(color: AppColors.primary, width: 3),
              ),
            ),
            child: Text(
              usuario != null ? '${usuario.nombreCompleto} · SUPER_ADMIN' : 'SUPER_ADMIN',
              style: GoogleFonts.inter(
                fontWeight: FontWeight.w600,
                fontSize: 13,
                color: AppColors.textDark,
              ),
            ),
          ),
          Expanded(
            child: GridView.builder(
              padding: const EdgeInsets.all(16),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
                childAspectRatio: 1.1,
              ),
              itemCount: secciones.length,
              itemBuilder: (context, index) {
                final seccion = secciones[index];
                return _TarjetaSeccion(
                  seccion: seccion,
                  onTap: () {
                    switch (seccion.clave) {
                      case 'dashboard':
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const DashboardHomeScreen(),
                          ),
                        );
                        break;
                      case 'usuarios':
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const UserManagementScreen(),
                          ),
                        );
                        break;
                      case 'productos':
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const ProductManagementScreen(),
                          ),
                        );
                        break;
                      case 'atributos':
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const AttributeManagementScreen(),
                          ),
                        );
                        break;
                      case 'permisos':
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const PermissionManagementScreen(),
                          ),
                        );
                        break;
                      case 'bitacora':
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const BitacoraListScreen(),
                          ),
                        );
                        break;
                      case 'clientes':
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const ClientListScreen(),
                          ),
                        );
                        break;
                      case 'inventario':
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const InventoryScreen(),
                          ),
                        );
                        break;
                      case 'reservas':
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const ReservationManagementScreen(),
                          ),
                        );
                        break;
                      case 'sucursales':
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const BranchManagementScreen(),
                          ),
                        );
                        break;
                      case 'proveedores':
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const SupplierManagementScreen(),
                          ),
                        );
                        break;
                      default:
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text('${seccion.titulo}: próximamente'),
                          ),
                        );
                    }
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _SeccionAdmin {
  final String titulo;
  final IconData icono;
  final String? clave;

  _SeccionAdmin(this.titulo, this.icono, this.clave);
}

class _TarjetaSeccion extends StatelessWidget {
  final _SeccionAdmin seccion;
  final VoidCallback onTap;

  const _TarjetaSeccion({required this.seccion, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.white,
      borderRadius: BorderRadius.circular(6),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(6),
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(6),
            border: Border.all(color: AppColors.line),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.04),
                blurRadius: 6,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Column(
            children: [
              Container(
                height: 3,
                decoration: const BoxDecoration(
                  color: AppColors.primary,
                  borderRadius: BorderRadius.vertical(top: Radius.circular(6)),
                ),
              ),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(seccion.icono, size: 30, color: AppColors.primary),
                      const SizedBox(height: 12),
                      Text(
                        seccion.titulo,
                        textAlign: TextAlign.center,
                        style: GoogleFonts.inter(
                          fontWeight: FontWeight.w600,
                          fontSize: 13,
                          color: AppColors.textDark,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
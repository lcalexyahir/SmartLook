// mobile/lib/features/admin/presentation/admin_home_screen.dart
//
// MODIFICADO (SaaS - A.2): bajo el nombre y rol se muestran la empresa,
// la sucursal y el plan con su vencimiento (EmpresaBanner).
// MODIFICADO (SaaS): tarjeta "Empresas" (SUPER_ADMIN: lista de empresas con
// sus sucursales; ADMIN_EMPRESA: detalle de la suya) y se enlaza
// "Usuarios y Roles", que mostraba "próximamente".

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../../../core/services/auth_service.dart';
import '../../../shared/theme/app_colors.dart';
import '../../../shared/widgets/empresa_banner.dart';
import '../../pos/presentation/pos_cart_screen.dart';
import '../../deliveries/presentation/deliveries_screen.dart';
import '../../catalog/presentation/product_list_screen.dart';
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
import 'devolucion_list_screen.dart';
import 'empresa_list_screen.dart';
import 'empresa_detail_screen.dart';

class AdminHomeScreen extends StatelessWidget {
  const AdminHomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final authService = context.watch<AuthService>();
    final usuario = authService.currentUser;
    final esSuperAdmin = usuario?.hasRole('SUPER_ADMIN') ?? false;
    final esAdminEmpresa = usuario?.hasRole('ADMIN_EMPRESA') ?? false;

    final secciones = <_SeccionAdmin>[
      _SeccionAdmin('Dashboard', Icons.dashboard_outlined, 'dashboard'),
      if (esSuperAdmin || (esAdminEmpresa && usuario?.idEmpresa != null))
        _SeccionAdmin(esSuperAdmin ? 'Empresas' : 'Mi empresa', Icons.business_outlined, 'empresas'),
      _SeccionAdmin('Catálogo', Icons.shopping_bag_outlined, 'catalogo'),
      _SeccionAdmin('Punto de Venta', Icons.point_of_sale_outlined, 'pos'),
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
      if (usuario != null && (usuario.hasRole('SUPER_ADMIN') || usuario.hasRole('ADMIN_EMPRESA') || usuario.hasRole('ENCARGADO_SUCURSAL')))
        _SeccionAdmin('Entregas', Icons.delivery_dining, 'entregas'),
      // Devoluciones: misma restricción de rol que "Entregas".
      if (usuario != null && (usuario.hasRole('SUPER_ADMIN') || usuario.hasRole('ADMIN_EMPRESA') || usuario.hasRole('ENCARGADO_SUCURSAL')))
        _SeccionAdmin('Devoluciones', Icons.assignment_return_outlined, 'devoluciones'),
    ];

    final nombreRol = usuario != null && usuario.roles.isNotEmpty
        ? usuario.roles.first.nombre
        : '';

    void abrir(Widget pantalla) {
      Navigator.push(context, MaterialPageRoute(builder: (context) => pantalla));
    }

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
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  usuario != null ? '${usuario.nombreCompleto} · $nombreRol' : nombreRol,
                  style: GoogleFonts.inter(
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                    color: AppColors.textDark,
                  ),
                ),
                if (usuario?.empresaNombre != null) ...[
                  const SizedBox(height: 8),
                  const EmpresaBanner(),
                ],
              ],
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
                        abrir(const DashboardHomeScreen());
                        break;
                      case 'empresas':
                        if (esSuperAdmin) {
                          abrir(const EmpresaListScreen());
                        } else if (usuario?.idEmpresa != null) {
                          abrir(EmpresaDetailScreen(idEmpresa: usuario!.idEmpresa!));
                        }
                        break;
                      case 'catalogo':
                        abrir(const ProductListScreen());
                        break;
                      case 'pos':
                        abrir(const PosCartScreen());
                        break;
                      case 'usuarios':
                        abrir(const UserManagementScreen());
                        break;
                      case 'productos':
                        abrir(const ProductManagementScreen());
                        break;
                      case 'atributos':
                        abrir(const AttributeManagementScreen());
                        break;
                      case 'permisos':
                        abrir(const PermissionManagementScreen());
                        break;
                      case 'bitacora':
                        abrir(const BitacoraListScreen());
                        break;
                      case 'clientes':
                        abrir(const ClientListScreen());
                        break;
                      case 'inventario':
                        abrir(const InventoryScreen());
                        break;
                      case 'reservas':
                        abrir(const ReservationManagementScreen());
                        break;
                      case 'sucursales':
                        abrir(const BranchManagementScreen());
                        break;
                      case 'entregas':
                        abrir(const DeliveriesScreen());
                        break;
                      case 'devoluciones':
                        abrir(const DevolucionListScreen());
                        break;
                      case 'proveedores':
                        abrir(const SupplierManagementScreen());
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
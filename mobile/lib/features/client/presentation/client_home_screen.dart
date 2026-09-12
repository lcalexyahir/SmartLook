// mobile/lib/features/client/presentation/client_home_screen.dart
//
// MODIFICADO (CU11/CU12/CU13): la pestaña "Reservas" ya no es
// placeholder - ahora es ReservationStatusScreen (lista + cancelar +
// botón flotante para crear una nueva). "Perfil" sigue como placeholder,
// listo para cuando se construya ese caso de uso.

import 'package:flutter/material.dart';
import '../../catalog/presentation/product_list_screen.dart';
import '../../reservations/presentation/reservation_status_screen.dart';
import '../../../shared/theme/app_colors.dart';

class ClientHomeScreen extends StatefulWidget {
  const ClientHomeScreen({super.key});

  @override
  State<ClientHomeScreen> createState() => _ClientHomeScreenState();
}

class _ClientHomeScreenState extends State<ClientHomeScreen> {
  int _indiceActual = 0;

  final List<Widget> _pantallas = const [
    ProductListScreen(),
    ReservationStatusScreen(),
    _SeccionProximamente(titulo: 'Perfil', icono: Icons.person_outline),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _indiceActual,
        children: _pantallas,
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _indiceActual,
        selectedItemColor: AppColors.primary,
        unselectedItemColor: Colors.grey,
        onTap: (index) => setState(() => _indiceActual = index),
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.checkroom_outlined),
            label: 'Catálogo',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.event_available_outlined),
            label: 'Reservas',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person_outline),
            label: 'Perfil',
          ),
        ],
      ),
    );
  }
}

class _SeccionProximamente extends StatelessWidget {
  final String titulo;
  final IconData icono;

  const _SeccionProximamente({required this.titulo, required this.icono});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(titulo)),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icono, size: 56, color: Colors.grey.shade400),
            const SizedBox(height: 12),
            Text(
              '$titulo: próximamente',
              style: const TextStyle(color: Colors.grey, fontSize: 15),
            ),
          ],
        ),
      ),
    );
  }
}
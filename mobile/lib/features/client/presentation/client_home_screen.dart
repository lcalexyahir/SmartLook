// mobile/lib/features/client/presentation/client_home_screen.dart
//
// MODIFICADO (CU18/CU19): se agrega el globo de chat del asistente virtual,
// visible solo en la pestaña Catálogo (índice 0).
import 'package:flutter/material.dart';
import '../../ai_assistant/presentation/chat_bubble_fab.dart';
import '../../catalog/presentation/product_list_screen.dart';
import '../../reservations/presentation/reservation_status_screen.dart';
import '../../orders/presentation/orders_screen.dart';
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
    OrdersScreen(),
    _SeccionProximamente(titulo: 'Perfil', icono: Icons.person_outline),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _indiceActual,
        children: _pantallas,
      ),
      floatingActionButton: _indiceActual == 0 ? const ChatBubbleFab() : null,
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
            icon: Icon(Icons.receipt_long_outlined),
            label: 'Pedidos',
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
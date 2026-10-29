// mobile/lib/features/client/presentation/client_home_screen.dart
//
// MODIFICADO (CU18/CU19): globo de chat del asistente virtual, visible solo
// en la pestaña Catálogo (índice 0).
// MODIFICADO (perfil): la pestaña Perfil muestra la pantalla real; se
// recarga al abrirla para que el historial incluya las compras nuevas.
import 'package:flutter/material.dart';
import '../../ai_assistant/presentation/chat_bubble_fab.dart';
import '../../catalog/presentation/product_list_screen.dart';
import '../../reservations/presentation/reservation_status_screen.dart';
import '../../orders/presentation/orders_screen.dart';
import '../../../shared/theme/app_colors.dart';
import 'profile_screen.dart';

class ClientHomeScreen extends StatefulWidget {
  const ClientHomeScreen({super.key});

  @override
  State<ClientHomeScreen> createState() => _ClientHomeScreenState();
}

class _ClientHomeScreenState extends State<ClientHomeScreen> {
  static const int _indicePedidos = 2;
  static const int _indicePerfil = 3;

  int _indiceActual = 0;
  final GlobalKey<ProfileScreenState> _perfilKey = GlobalKey<ProfileScreenState>();
  late final List<Widget> _pantallas;

  @override
  void initState() {
    super.initState();
    _pantallas = [
      const ProductListScreen(),
      const ReservationStatusScreen(),
      const OrdersScreen(),
      ProfileScreen(
        key: _perfilKey,
        onVerPedidos: () => _irA(_indicePedidos),
      ),
    ];
  }

  void _irA(int index) {
    setState(() => _indiceActual = index);
    if (index == _indicePerfil) {
      _perfilKey.currentState?.recargar();
    }
  }

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
        onTap: _irA,
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
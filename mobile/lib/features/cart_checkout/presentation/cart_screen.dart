// mobile/lib/features/cart_checkout/presentation/cart_screen.dart
//
// Archivo NUEVO (estaba vacío). Lista el carrito activo del cliente,
// permite +/- cantidad y quitar items.

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/network/api_client.dart';
import '../../../shared/theme/app_colors.dart';
import '../data/cart_service.dart';

class CartScreen extends StatefulWidget {
  const CartScreen({super.key});

  @override
  State<CartScreen> createState() => _CartScreenState();
}

class _CartScreenState extends State<CartScreen> {
  late final CartService _cartService;
  Map<String, dynamic>? _carrito;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    final apiClient = context.read<ApiClient>();
    _cartService = CartService(apiClient: apiClient);
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() => _loading = true);
    try {
      final carrito = await _cartService.getCarritoActual();
      setState(() {
        _carrito = carrito;
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  Future<void> _incrementar(Map<String, dynamic> item) async {
    await _cartService.actualizarCantidad(item['id_item'] as int, (item['cantidad'] as int) + 1);
    _cargar();
  }

  Future<void> _decrementar(Map<String, dynamic> item) async {
    final cantidad = item['cantidad'] as int;
    if (cantidad <= 1) {
      await _quitar(item);
      return;
    }
    await _cartService.actualizarCantidad(item['id_item'] as int, cantidad - 1);
    _cargar();
  }

  Future<void> _quitar(Map<String, dynamic> item) async {
    await _cartService.quitarItem(item['id_item'] as int);
    _cargar();
  }

  @override
  Widget build(BuildContext context) {
    final items = (_carrito?['items'] ?? []) as List<dynamic>;
    return Scaffold(
      appBar: AppBar(title: const Text('Mi Carrito')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : items.isEmpty
              ? const Center(child: Text('Tu carrito está vacío.'))
              : RefreshIndicator(
                  onRefresh: _cargar,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: items.length,
                    itemBuilder: (context, index) {
                      final item = items[index] as Map<String, dynamic>;
                      return Card(
                        margin: const EdgeInsets.only(bottom: 12),
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Row(
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      item['variante'].toString(),
                                      style: const TextStyle(fontWeight: FontWeight.w600),
                                    ),
                                    Text(
                                      'Bs ${item['precio_unitario']} c/u',
                                      style: const TextStyle(color: AppColors.grey, fontSize: 12),
                                    ),
                                  ],
                                ),
                              ),
                              IconButton(
                                icon: const Icon(Icons.remove_circle_outline),
                                onPressed: () => _decrementar(item),
                              ),
                              Text('${item['cantidad']}'),
                              IconButton(
                                icon: const Icon(Icons.add_circle_outline),
                                onPressed: () => _incrementar(item),
                              ),
                              const SizedBox(width: 8),
                              Text(
                                'Bs ${item['subtotal']}',
                                style: const TextStyle(fontWeight: FontWeight.w700),
                              ),
                              IconButton(
                                icon: const Icon(Icons.close, color: AppColors.danger),
                                onPressed: () => _quitar(item),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
      bottomNavigationBar: _carrito == null || items.isEmpty
          ? null
          : Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Total', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
                      Text(
                        'Bs ${_carrito!['total']}',
                        style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: AppColors.accent),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  ElevatedButton(
                    onPressed: null,
                    style: ElevatedButton.styleFrom(minimumSize: const Size(double.infinity, 50)),
                    child: const Text('Proceder al Pago (próximamente)'),
                  ),
                ],
              ),
            ),
    );
  }
}
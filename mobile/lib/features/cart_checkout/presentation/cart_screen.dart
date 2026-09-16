// mobile/lib/features/cart_checkout/presentation/cart_screen.dart

import 'package:flutter/material.dart';
import 'package:flutter_stripe/flutter_stripe.dart' hide Card;
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

  List<dynamic> _sucursales = [];
  int? _sucursalSeleccionada;
  String? _errorPago;
  Map<String, dynamic>? _ordenConfirmada;

  // Flujo de pago con Stripe
  bool _mostrarFormularioPago = false;
  bool _iniciandoPago = false;
  bool _confirmandoPago = false;
  String? _clientSecret;
  bool _tarjetaCompleta = false;

  @override
  void initState() {
    super.initState();
    final apiClient = context.read<ApiClient>();
    _cartService = CartService(apiClient: apiClient);
    _cargar();
    _cargarSucursales();
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

  Future<void> _cargarSucursales() async {
    try {
      final sucursales = await _cartService.getSucursales();
      setState(() => _sucursales = sucursales);
    } catch (_) {
      setState(() => _sucursales = []);
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

  String _extraerError(Object e, String fallback) {
    try {
      final data = (e as dynamic).response?.data;
      if (data is Map && data['error'] != null) return data['error'].toString();
    } catch (_) {}
    return fallback;
  }

  // Paso 1: crea el intento de pago y muestra el formulario de tarjeta.
  Future<void> _iniciarPago() async {
    if (_sucursalSeleccionada == null) {
      setState(() => _errorPago = 'Selecciona una sucursal de entrega/retiro.');
      return;
    }
    setState(() {
      _iniciandoPago = true;
      _errorPago = null;
    });
    try {
      final data = await _cartService.checkout(_sucursalSeleccionada!);
      setState(() {
        _clientSecret = data['client_secret'] as String;
        _mostrarFormularioPago = true;
        _iniciandoPago = false;
      });
    } catch (e) {
      setState(() {
        _errorPago = _extraerError(e, 'No se pudo iniciar el pago. Intenta nuevamente.');
        _iniciandoPago = false;
      });
    }
  }

  // Paso 2: confirma la tarjeta con Stripe y cierra la orden en el backend.
  Future<void> _confirmarPago() async {
    if (_clientSecret == null || !_tarjetaCompleta) return;
    setState(() {
      _confirmandoPago = true;
      _errorPago = null;
    });
    try {
      final paymentIntent = await Stripe.instance.confirmPayment(
        paymentIntentClientSecret: _clientSecret!,
        data: const PaymentMethodParams.card(
          paymentMethodData: PaymentMethodData(),
        ),
      );

      final orden = await _cartService.confirmarPago(paymentIntent.id);
      setState(() {
        _ordenConfirmada = orden;
        _mostrarFormularioPago = false;
        _confirmandoPago = false;
      });
      _cargar();
    } on StripeException catch (e) {
      setState(() {
        _errorPago = e.error.localizedMessage ?? 'La tarjeta fue rechazada.';
        _confirmandoPago = false;
      });
    } catch (e) {
      setState(() {
        _errorPago = _extraerError(e, 'No se pudo cerrar la orden.');
        _confirmandoPago = false;
      });
    }
  }

  void _cancelarPago() {
    setState(() {
      _mostrarFormularioPago = false;
      _clientSecret = null;
      _errorPago = null;
      _tarjetaCompleta = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_ordenConfirmada != null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Mi Carrito')),
        body: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.check_circle, color: Colors.green, size: 64),
              const SizedBox(height: 16),
              const Text('¡Compra realizada con éxito!', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              Text('Orden #${_ordenConfirmada!['id_orden']} - Total Bs ${_ordenConfirmada!['total']}'),
              const SizedBox(height: 4),
              Text('Referencia de pago (Stripe): ${_ordenConfirmada!['referencia_pago']}'),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: () => setState(() => _ordenConfirmada = null),
                child: const Text('Seguir comprando'),
              ),
            ],
          ),
        ),
      );
    }

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
          : SingleChildScrollView(
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

                  // Paso 1: elegir sucursal
                  if (!_mostrarFormularioPago) ...[
                    DropdownButtonFormField<int>(
                      value: _sucursalSeleccionada,
                      decoration: const InputDecoration(
                        labelText: 'Sucursal de entrega/retiro',
                        border: OutlineInputBorder(),
                      ),
                      items: _sucursales
                          .map((s) => DropdownMenuItem<int>(
                                value: s['id_sucursal'] as int,
                                child: Text(s['nombre'].toString()),
                              ))
                          .toList(),
                      onChanged: (value) => setState(() => _sucursalSeleccionada = value),
                    ),
                  ],

                  if (_errorPago != null) ...[
                    const SizedBox(height: 8),
                    Text(_errorPago!, style: const TextStyle(color: AppColors.danger)),
                  ],

                  const SizedBox(height: 12),

                  if (!_mostrarFormularioPago)
                    ElevatedButton(
                      onPressed: _iniciandoPago ? null : _iniciarPago,
                      style: ElevatedButton.styleFrom(minimumSize: const Size(double.infinity, 50)),
                      child: Text(_iniciandoPago ? 'Preparando pago...' : 'Continuar al pago'),
                    ),

                  // Paso 2: campo de tarjeta real (SDK de Stripe)
                  if (_mostrarFormularioPago) ...[
                    const Text('Datos de la tarjeta', style: TextStyle(fontWeight: FontWeight.w600)),
                    const SizedBox(height: 8),
                    CardField(
                      enablePostalCode: false,
                      numberHintText: '4242 4242 4242 4242',
                      onCardChanged: (details) {
                        setState(() => _tarjetaCompleta = details?.complete ?? false);
                      },
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Tarjeta de prueba: 4242 4242 4242 4242, fecha futura y CVC.',
                      style: TextStyle(fontSize: 12, color: AppColors.grey),
                    ),
                    const SizedBox(height: 12),
                    ElevatedButton(
                      onPressed: (_confirmandoPago || !_tarjetaCompleta) ? null : _confirmarPago,
                      style: ElevatedButton.styleFrom(minimumSize: const Size(double.infinity, 50)),
                      child: Text(_confirmandoPago ? 'Procesando pago...' : 'Pagar Bs ${_carrito!['total']}'),
                    ),
                    TextButton(
                      onPressed: _confirmandoPago ? null : _cancelarPago,
                      child: const Text('Cancelar'),
                    ),
                  ],
                ],
              ),
            ),
    );
  }
}
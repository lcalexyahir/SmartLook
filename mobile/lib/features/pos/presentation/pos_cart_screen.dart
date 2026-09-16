// mobile/lib/features/pos/presentation/pos_cart_screen.dart

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:qr_flutter/qr_flutter.dart';
import '../../../core/network/api_client.dart';
import '../../../shared/theme/app_colors.dart';
import '../../admin/data/inventory_service.dart';
import '../data/pos_sale_service.dart';

class ItemVenta {
  final int idVariante;
  final String nombre;
  final double precio;
  int cantidad;

  ItemVenta({required this.idVariante, required this.nombre, required this.precio, this.cantidad = 1});
}

class PosCartScreen extends StatefulWidget {
  const PosCartScreen({super.key});

  @override
  State<PosCartScreen> createState() => _PosCartScreenState();
}

class _PosCartScreenState extends State<PosCartScreen> {
  late final InventoryService _inventoryService;
  late final PosSaleService _posSaleService;

  final TextEditingController _busquedaController = TextEditingController();
  List<dynamic> _resultados = [];
  bool _buscando = false;

  final List<ItemVenta> _items = [];
  List<dynamic> _sucursales = [];
  int? _sucursalSeleccionada;
  String _metodoPago = 'EFECTIVO';

  bool _registrando = false;
  String? _error;
  Map<String, dynamic>? _ventaConfirmada;

  @override
  void initState() {
    super.initState();
    final apiClient = context.read<ApiClient>();
    _inventoryService = InventoryService(apiClient: apiClient);
    _posSaleService = PosSaleService(apiClient: apiClient);
    _cargarSucursales();
  }

  Future<void> _cargarSucursales() async {
    try {
      final sucursales = await _inventoryService.getSucursales();
      setState(() => _sucursales = sucursales);
    } catch (_) {
      setState(() => _sucursales = []);
    }
  }

  Future<void> _buscar() async {
    final termino = _busquedaController.text.trim();
    if (termino.isEmpty) {
      setState(() => _resultados = []);
      return;
    }
    setState(() => _buscando = true);
    try {
      final resultados = await _inventoryService.getVariantes(busqueda: termino);
      setState(() {
        _resultados = resultados;
        _buscando = false;
      });
    } catch (_) {
      setState(() {
        _resultados = [];
        _buscando = false;
      });
    }
  }

  void _agregarItem(Map<String, dynamic> variante) {
    final idVariante = variante['id_variante'] as int;
    final existente = _items.where((i) => i.idVariante == idVariante).firstOrNull;
    if (existente != null) {
      setState(() => existente.cantidad += 1);
    } else {
      setState(() {
        _items.add(ItemVenta(
          idVariante: idVariante,
          nombre: variante['nombre_completo'].toString(),
          precio: double.parse(variante['precio'].toString()),
        ));
      });
    }
  }

  void _incrementar(ItemVenta item) => setState(() => item.cantidad += 1);

  void _decrementar(ItemVenta item) {
    if (item.cantidad <= 1) {
      _quitar(item);
      return;
    }
    setState(() => item.cantidad -= 1);
  }

  void _quitar(ItemVenta item) => setState(() => _items.remove(item));

  double get _total => _items.fold(0.0, (acc, item) => acc + item.precio * item.cantidad);

  String get _qrData =>
      'SmartLook - Pago QR\nTotal: Bs ${_total.toStringAsFixed(2)}\nReferencia: SL-${DateTime.now().millisecondsSinceEpoch}';

  Future<void> _registrarVenta() async {
    if (_items.isEmpty) {
      setState(() => _error = 'Agrega al menos una prenda a la venta.');
      return;
    }
    if (_sucursalSeleccionada == null) {
      setState(() => _error = 'Selecciona la sucursal.');
      return;
    }

    setState(() {
      _registrando = true;
      _error = null;
    });

    try {
      final venta = await _posSaleService.registrarVenta(
        idSucursal: _sucursalSeleccionada!,
        metodoPago: _metodoPago,
        items: _items.map((i) => {'id_variante': i.idVariante, 'cantidad': i.cantidad}).toList(),
      );
      setState(() {
        _ventaConfirmada = venta;
        _registrando = false;
      });
    } catch (e) {
      String mensaje = 'No se pudo registrar la venta. Intenta nuevamente.';
      try {
        final data = (e as dynamic).response?.data;
        if (data is Map && data['error'] != null) mensaje = data['error'].toString();
      } catch (_) {}
      setState(() {
        _error = mensaje;
        _registrando = false;
      });
    }
  }

  void _nuevaVenta() {
    setState(() {
      _items.clear();
      _busquedaController.clear();
      _resultados = [];
      _sucursalSeleccionada = null;
      _metodoPago = 'EFECTIVO';
      _ventaConfirmada = null;
      _error = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_ventaConfirmada != null) {
      final venta = _ventaConfirmada!;
      final items = (venta['items'] ?? []) as List<dynamic>;
      return Scaffold(
        appBar: AppBar(title: const Text('Punto de Venta')),
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const Icon(Icons.check_circle, color: Colors.green, size: 56),
            const SizedBox(height: 12),
            Text('Venta #${venta['id_venta']} - ${venta['sucursal']}', style: const TextStyle(fontWeight: FontWeight.w600)),
            Text('Cajero: ${venta['usuario']}'),
            Text('Método de pago: ${venta['metodo_pago']}'),
            const SizedBox(height: 12),
            ...items.map((item) => ListTile(
                  title: Text(item['variante'].toString()),
                  subtitle: Text('x${item['cantidad']} - Bs ${item['precio_unitario']}'),
                  trailing: Text('Bs ${item['subtotal']}', style: const TextStyle(fontWeight: FontWeight.w600)),
                )),
            const Divider(),
            Text('Total: Bs ${venta['total']}', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: _nuevaVenta,
              style: ElevatedButton.styleFrom(minimumSize: const Size(double.infinity, 50)),
              child: const Text('Nueva venta'),
            ),
          ],
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Punto de Venta')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('Buscar prenda (código o nombre)', style: TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _busquedaController,
                  decoration: const InputDecoration(
                    hintText: 'Ej: CAM-001 o Camisa Oxford',
                    border: OutlineInputBorder(),
                  ),
                  onSubmitted: (_) => _buscar(),
                ),
              ),
              const SizedBox(width: 8),
              ElevatedButton(onPressed: _buscar, child: const Text('Buscar')),
            ],
          ),
          if (_buscando) const Padding(padding: EdgeInsets.all(12), child: Center(child: CircularProgressIndicator())),
          ..._resultados.map((r) => Card(
                margin: const EdgeInsets.only(top: 8),
                child: ListTile(
                  title: Text(r['nombre_completo'].toString()),
                  subtitle: Text('Bs ${r['precio']} - Stock: ${r['cantidad']}'),
                  trailing: ElevatedButton(
                    onPressed: () => _agregarItem(r),
                    child: const Text('Agregar'),
                  ),
                ),
              )),

          const SizedBox(height: 20),
          const Divider(),
          const Text('Venta actual', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
          const SizedBox(height: 8),

          if (_items.isEmpty) const Text('Sin prendas agregadas.', style: TextStyle(color: AppColors.grey)),

          ..._items.map((item) => Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: Padding(
                  padding: const EdgeInsets.all(8),
                  child: Row(
                    children: [
                      Expanded(child: Text(item.nombre, style: const TextStyle(fontWeight: FontWeight.w600))),
                      IconButton(icon: const Icon(Icons.remove_circle_outline), onPressed: () => _decrementar(item)),
                      Text('${item.cantidad}'),
                      IconButton(icon: const Icon(Icons.add_circle_outline), onPressed: () => _incrementar(item)),
                      Text('Bs ${(item.precio * item.cantidad).toStringAsFixed(2)}', style: const TextStyle(fontWeight: FontWeight.w700)),
                      IconButton(icon: const Icon(Icons.close, color: AppColors.danger), onPressed: () => _quitar(item)),
                    ],
                  ),
                ),
              )),

          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Total', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
              Text('Bs ${_total.toStringAsFixed(2)}', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.accent)),
            ],
          ),
          const SizedBox(height: 16),

          DropdownButtonFormField<int>(
            value: _sucursalSeleccionada,
            decoration: const InputDecoration(labelText: 'Sucursal', border: OutlineInputBorder()),
            items: _sucursales
                .map((s) => DropdownMenuItem<int>(value: s['id_sucursal'] as int, child: Text(s['nombre'].toString())))
                .toList(),
            onChanged: (value) => setState(() => _sucursalSeleccionada = value),
          ),
          const SizedBox(height: 12),

          DropdownButtonFormField<String>(
            value: _metodoPago,
            decoration: const InputDecoration(labelText: 'Método de pago', border: OutlineInputBorder()),
            items: const [
              DropdownMenuItem(value: 'EFECTIVO', child: Text('Efectivo')),
              DropdownMenuItem(value: 'TARJETA', child: Text('Tarjeta (datáfono físico)')),
              DropdownMenuItem(value: 'QR', child: Text('QR')),
            ],
            onChanged: (value) => setState(() => _metodoPago = value ?? 'EFECTIVO'),
          ),

          if (_metodoPago == 'QR' && _items.isNotEmpty) ...[
            const SizedBox(height: 16),
            const Text(
              'Mostrale este código al cliente para que pague desde su app bancaria.',
              style: TextStyle(fontSize: 12, color: AppColors.grey),
            ),
            const SizedBox(height: 8),
            Center(
              child: QrImageView(
                data: _qrData,
                size: 180,
              ),
            ),
          ],

          if (_error != null) ...[
            const SizedBox(height: 12),
            Text(_error!, style: const TextStyle(color: AppColors.danger)),
          ],

          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _registrando ? null : _registrarVenta,
            style: ElevatedButton.styleFrom(minimumSize: const Size(double.infinity, 50)),
            child: Text(_registrando ? 'Registrando...' : 'Registrar Venta'),
          ),
        ],
      ),
    );
  }
}
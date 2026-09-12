// mobile/lib/features/reservations/presentation/reservation_form_screen.dart
//
// Archivo NUEVO (estaba vacío). Formulario para que el cliente agregue
// varias prendas, elija sucursal/fecha/hora y confirme la reserva.
// Sigue el mismo patrón que product_detail_screen.dart: llamadas
// directas con apiClient.dio para catálogo/sucursales, y el servicio
// dedicado (ReservationService) para la reserva en sí.

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/network/api_client.dart';
import '../../../shared/theme/app_colors.dart';
import '../data/reservation_service.dart';

class ReservationFormScreen extends StatefulWidget {
  const ReservationFormScreen({super.key});

  @override
  State<ReservationFormScreen> createState() => _ReservationFormScreenState();
}

class _ReservationFormScreenState extends State<ReservationFormScreen> {
  late final ReservationService _reservationService;

  List<dynamic> _productos = [];
  List<dynamic> _sucursales = [];

  int? _productoSeleccionado;
  int? _varianteSeleccionada;
  int? _sucursalSeleccionada;
  DateTime? _fecha;
  TimeOfDay? _hora;

  final List<Map<String, dynamic>> _items = [];

  bool _loading = true;
  bool _enviando = false;
  String _error = '';
  String _exito = '';

  @override
  void initState() {
    super.initState();
    final apiClient = context.read<ApiClient>();
    _reservationService = ReservationService(apiClient: apiClient);
    _cargarDatos();
  }

  Future<void> _cargarDatos() async {
    final apiClient = context.read<ApiClient>();
    try {
      final productosResp = await apiClient.dio.get('/catalog/productos/');
      final sucursalesResp = await apiClient.dio.get('/catalog/sucursales/');
      setState(() {
        _productos = (productosResp.data['results'] ?? productosResp.data) as List<dynamic>;
        _sucursales = (sucursalesResp.data['results'] ?? sucursalesResp.data) as List<dynamic>;
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  dynamic get _productoActual {
    if (_productoSeleccionado == null) return null;
    return _productos.firstWhere(
      (p) => p['id_producto'] == _productoSeleccionado,
      orElse: () => null,
    );
  }

  void _agregarItem() {
    setState(() => _error = '');
    final producto = _productoActual;
    if (producto == null || _varianteSeleccionada == null) {
      setState(() => _error = 'Selecciona un producto y una variante.');
      return;
    }
    final variantes = (producto['variantes'] ?? []) as List<dynamic>;
    final variante = variantes.firstWhere(
      (v) => v['id_variante'] == _varianteSeleccionada,
      orElse: () => null,
    );
    if (variante == null) return;
    final yaAgregada = _items.any((i) => i['id_variante'] == variante['id_variante']);
    if (yaAgregada) {
      setState(() => _error = 'Esa prenda ya está en la reserva.');
      return;
    }
    setState(() {
      _items.add({
        'id_variante': variante['id_variante'],
        'label': producto['nombre'].toString() +
            ' - ' +
            (variante['talla']?['nombre'] ?? '').toString() +
            ' - ' +
            (variante['color']?['nombre'] ?? '').toString(),
      });
      _varianteSeleccionada = null;
    });
  }

  void _quitarItem(int index) {
    setState(() => _items.removeAt(index));
  }

  Future<void> _elegirFecha() async {
    final seleccionada = await showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 90)),
    );
    if (seleccionada != null) {
      setState(() => _fecha = seleccionada);
    }
  }

  Future<void> _elegirHora() async {
    final seleccionada = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.now(),
    );
    if (seleccionada != null) {
      setState(() => _hora = seleccionada);
    }
  }

  Future<void> _enviar() async {
    setState(() {
      _error = '';
      _exito = '';
    });
    if (_sucursalSeleccionada == null) {
      setState(() => _error = 'Selecciona una sucursal.');
      return;
    }
    if (_fecha == null || _hora == null) {
      setState(() => _error = 'Selecciona fecha y hora.');
      return;
    }
    if (_items.isEmpty) {
      setState(() => _error = 'Agrega al menos una prenda a la reserva.');
      return;
    }

    final fechaStr = _fecha!.year.toString().padLeft(4, '0') +
        '-' +
        _fecha!.month.toString().padLeft(2, '0') +
        '-' +
        _fecha!.day.toString().padLeft(2, '0');
    final horaStr =
        _hora!.hour.toString().padLeft(2, '0') + ':' + _hora!.minute.toString().padLeft(2, '0');

    setState(() => _enviando = true);
    try {
      await _reservationService.crearReserva(
        idSucursal: _sucursalSeleccionada!,
        fechaReserva: fechaStr,
        horaReserva: horaStr,
        variantesIds: _items.map((i) => i['id_variante'] as int).toList(),
      );
      setState(() {
        _enviando = false;
        _exito = 'Reserva creada correctamente. Te esperamos en la sucursal elegida.';
        _items.clear();
        _sucursalSeleccionada = null;
        _fecha = null;
        _hora = null;
      });
    } catch (e) {
      setState(() {
        _enviando = false;
        _error = 'No se pudo crear la reserva. Intenta nuevamente.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Reservar Prendas')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Agregar Prenda', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<int>(
                    value: _productoSeleccionado,
                    decoration: const InputDecoration(labelText: 'Producto', border: OutlineInputBorder()),
                    items: _productos
                        .map<DropdownMenuItem<int>>((p) => DropdownMenuItem(
                              value: p['id_producto'] as int,
                              child: Text(p['nombre'].toString()),
                            ))
                        .toList(),
                    onChanged: (value) => setState(() {
                      _productoSeleccionado = value;
                      _varianteSeleccionada = null;
                    }),
                  ),
                  if (_productoActual != null) ...[
                    const SizedBox(height: 12),
                    DropdownButtonFormField<int>(
                      value: _varianteSeleccionada,
                      decoration: const InputDecoration(labelText: 'Talla / Color', border: OutlineInputBorder()),
                      items: ((_productoActual['variantes'] ?? []) as List<dynamic>)
                          .map<DropdownMenuItem<int>>((v) => DropdownMenuItem(
                                value: v['id_variante'] as int,
                                child: Text('${v['talla']?['nombre']} - ${v['color']?['nombre']} (Bs ${v['precio']})'),
                              ))
                          .toList(),
                      onChanged: (value) => setState(() => _varianteSeleccionada = value),
                    ),
                  ],
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton(
                      onPressed: _agregarItem,
                      child: const Text('+ Agregar a la reserva'),
                    ),
                  ),
                  if (_items.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    const Text('Prendas en esta reserva', style: TextStyle(fontWeight: FontWeight.w600)),
                    ..._items.asMap().entries.map(
                          (entry) => ListTile(
                            contentPadding: EdgeInsets.zero,
                            title: Text(entry.value['label']),
                            trailing: IconButton(
                              icon: const Icon(Icons.close, color: AppColors.danger),
                              onPressed: () => _quitarItem(entry.key),
                            ),
                          ),
                        ),
                  ],
                  const Divider(height: 32),
                  const Text('Datos de la Reserva', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<int>(
                    value: _sucursalSeleccionada,
                    decoration: const InputDecoration(labelText: 'Sucursal', border: OutlineInputBorder()),
                    items: _sucursales
                        .map<DropdownMenuItem<int>>((s) => DropdownMenuItem(
                              value: s['id_sucursal'] as int,
                              child: Text(s['nombre'].toString()),
                            ))
                        .toList(),
                    onChanged: (value) => setState(() => _sucursalSeleccionada = value),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton(
                          onPressed: _elegirFecha,
                          child: Text(_fecha == null
                              ? 'Elegir fecha'
                              : '${_fecha!.day}/${_fecha!.month}/${_fecha!.year}'),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: OutlinedButton(
                          onPressed: _elegirHora,
                          child: Text(_hora == null ? 'Elegir hora' : _hora!.format(context)),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  if (_error.isNotEmpty)
                    Text(_error, style: const TextStyle(color: AppColors.danger)),
                  if (_exito.isNotEmpty)
                    Text(_exito, style: const TextStyle(color: AppColors.success)),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: _enviando ? null : _enviar,
                    style: ElevatedButton.styleFrom(minimumSize: const Size(double.infinity, 50)),
                    child: Text(_enviando ? 'Enviando...' : 'Confirmar Reserva'),
                  ),
                ],
              ),
            ),
    );
  }
}
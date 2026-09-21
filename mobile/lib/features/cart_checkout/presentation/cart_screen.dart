// mobile/lib/features/cart_checkout/presentation/cart_screen.dart

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart'
    show
        FlutterMap,
        MapController,
        MapOptions,
        Marker,
        MarkerLayer,
        RichAttributionWidget,
        TextSourceAttribution,
        TileLayer;
import 'package:flutter_stripe/flutter_stripe.dart' hide Card;
import 'package:geolocator/geolocator.dart'
    show Geolocator, LocationAccuracy, LocationPermission, LocationSettings;
import 'package:latlong2/latlong.dart' show LatLng;
import 'package:provider/provider.dart';
import '../../../core/network/api_client.dart';
import '../../../shared/theme/app_colors.dart';
import '../data/cart_service.dart';

class _MensajeError implements Exception {
  final String texto;
  const _MensajeError(this.texto);
}

class CartScreen extends StatefulWidget {
  const CartScreen({super.key});

  @override
  State<CartScreen> createState() => _CartScreenState();
}

class _CartScreenState extends State<CartScreen> {
  late final CartService _cartService;
  final MapController _mapController = MapController();
  final TextEditingController _direccionCtrl = TextEditingController();
  final TextEditingController _referenciaCtrl = TextEditingController();

  // Santa Cruz de la Sierra: centro del mapa cuando aún no hay sucursal ni punto.
  static const LatLng _centroDefecto = LatLng(-17.7834, -63.1821);

  Map<String, dynamic>? _carrito;
  bool _loading = true;

  List<dynamic> _sucursales = [];
  int? _sucursalSeleccionada;
  String? _errorPago;
  Map<String, dynamic>? _ordenConfirmada;

  // CU21: entrega
  String _tipoEntrega = 'RETIRO'; // RETIRO | DELIVERY
  double? _lat;
  double? _lng;
  bool _ubicando = false;
  bool _cotizando = false;
  Map<String, dynamic>? _cotizacion;
  int _geocodificacionId = 0;
  int _cotizacionId = 0;

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

  @override
  void dispose() {
    _direccionCtrl.dispose();
    _referenciaCtrl.dispose();
    _mapController.dispose();
    super.dispose();
  }

  // ---- Datos derivados ----

  LatLng? get _puntoCliente =>
      (_lat != null && _lng != null) ? LatLng(_lat!, _lng!) : null;

  LatLng? get _puntoSucursal {
    for (final s in _sucursales) {
      if (s['id_sucursal'] == _sucursalSeleccionada) {
        final lat = double.tryParse('${s['latitud']}');
        final lng = double.tryParse('${s['longitud']}');
        if (lat != null && lng != null) return LatLng(lat, lng);
      }
    }
    return null;
  }

  double get _totalProductos => double.tryParse('${_carrito?['total']}') ?? 0;

  double get _costoEnvio => (_tipoEntrega == 'DELIVERY' && _cotizacion != null)
      ? (double.tryParse('${_cotizacion!['costo_envio']}') ?? 0)
      : 0;

  double get _totalAPagar => _totalProductos + _costoEnvio;

  // ---- Carga ----

  Future<void> _cargar() async {
    // El spinner solo aparece la primera vez, para no destruir el mapa al cambiar cantidades.
    setState(() => _loading = _carrito == null);
    try {
      final carrito = await _cartService.getCarritoActual();
      if (!mounted) return;
      setState(() {
        _carrito = carrito;
        _loading = false;
      });
      final items = (carrito['items'] ?? []) as List<dynamic>;
      // Si cambió la cantidad de prendas, el costo de envío también puede cambiar.
      if (_tipoEntrega == 'DELIVERY' &&
          _lat != null &&
          _ordenConfirmada == null &&
          items.isNotEmpty) {
        _cotizar();
      }
    } catch (e) {
      if (!mounted) return;
      setState(() => _loading = false);
    }
  }

  Future<void> _cargarSucursales() async {
    try {
      final sucursales = await _cartService.getSucursales();
      if (!mounted) return;
      setState(() => _sucursales = sucursales);
    } catch (_) {
      if (!mounted) return;
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

  // ---- CU21: entrega ----

  void _onCambioTipo(String tipo) {
    setState(() {
      _tipoEntrega = tipo;
      _cotizacion = null;
      _errorPago = null;
    });
    // Al volver a Delivery con una ubicación ya elegida, se recotiza sola.
    if (tipo == 'DELIVERY' && _lat != null && _sucursalSeleccionada != null) {
      _cotizar();
    }
  }

  void _onCambioSucursal(int? value) {
    setState(() {
      _sucursalSeleccionada = value;
      _cotizacion = null;
      _errorPago = null;
    });
    if (_tipoEntrega == 'DELIVERY') {
      if (_lat != null) {
        _cotizar();
      } else {
        final p = _puntoSucursal;
        if (p != null) _moverMapa(p, 14);
      }
    }
  }

  void _moverMapa(LatLng punto, double zoom) {
    try {
      _mapController.move(punto, zoom);
    } catch (_) {
      // El mapa todavía no está dibujado: se centrará solo al construirse.
    }
  }

  // El cliente marcó un punto (GPS o toque en el mapa): se guarda, se completa
  // la dirección y se cotiza el envío.
  void _marcarPunto(LatLng p, {bool moverMapa = false}) {
    setState(() {
      _lat = p.latitude;
      _lng = p.longitude;
    });
    if (moverMapa) _moverMapa(p, 16);
    _completarDireccion(p);
    _cotizar();
  }

  Future<void> _usarMiUbicacion() async {
    setState(() {
      _ubicando = true;
      _errorPago = null;
    });
    try {
      if (!await Geolocator.isLocationServiceEnabled()) {
        throw const _MensajeError('Activa la ubicación (GPS) de tu teléfono e intenta de nuevo.');
      }
      var permiso = await Geolocator.checkPermission();
      if (permiso == LocationPermission.denied) {
        permiso = await Geolocator.requestPermission();
      }
      if (permiso == LocationPermission.denied ||
          permiso == LocationPermission.deniedForever) {
        throw const _MensajeError(
          'Permite el acceso a la ubicación para calcular tu envío. También puedes marcar el punto tocando el mapa.',
        );
      }
      final pos = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: Duration(seconds: 15),
        ),
      );
      if (!mounted) return;
      setState(() => _ubicando = false);
      _marcarPunto(LatLng(pos.latitude, pos.longitude), moverMapa: true);
    } on _MensajeError catch (e) {
      if (!mounted) return;
      setState(() {
        _ubicando = false;
        _errorPago = e.texto;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _ubicando = false;
        _errorPago = 'No se pudo obtener tu ubicación. Marca el punto tocando el mapa.';
      });
    }
  }

  // Rellena "Dirección de entrega" con la dirección del punto (OpenStreetMap).
  Future<void> _completarDireccion(LatLng p) async {
    final id = ++_geocodificacionId;
    final direccion = await _cartService.direccionDesdeCoordenadas(p.latitude, p.longitude);
    // Si el cliente movió el punto otra vez mientras esperaba, se descarta esta respuesta.
    if (!mounted || id != _geocodificacionId || direccion == null) return;
    setState(() => _direccionCtrl.text = direccion);
  }

  Future<void> _cotizar() async {
    if (_sucursalSeleccionada == null) {
      setState(() => _errorPago = 'Selecciona primero la sucursal que despacha tu pedido.');
      return;
    }
    if (_lat == null || _lng == null) return;
    final id = ++_cotizacionId;
    setState(() {
      _cotizando = true;
      _errorPago = null;
    });
    try {
      final data = await _cartService.cotizarEnvio(
        idSucursal: _sucursalSeleccionada!,
        latitud: _lat!,
        longitud: _lng!,
      );
      if (!mounted || id != _cotizacionId) return;
      setState(() {
        _cotizacion = data;
        _cotizando = false;
      });
    } catch (e) {
      if (!mounted || id != _cotizacionId) return;
      setState(() {
        _cotizacion = null;
        _cotizando = false;
        _errorPago = _extraerError(e, 'No se pudo cotizar el envío.');
      });
    }
  }

  void _reiniciarEntrega() {
    _tipoEntrega = 'RETIRO';
    _lat = null;
    _lng = null;
    _cotizacion = null;
    _direccionCtrl.clear();
    _referenciaCtrl.clear();
  }

  // ---- Pago ----

  // Paso 1: crea el intento de pago y muestra el formulario de tarjeta.
  Future<void> _iniciarPago() async {
    if (_sucursalSeleccionada == null) {
      setState(() => _errorPago = _tipoEntrega == 'DELIVERY'
          ? 'Selecciona la sucursal que despacha tu pedido.'
          : 'Selecciona una sucursal de entrega/retiro.');
      return;
    }

    Map<String, dynamic>? entrega;
    if (_tipoEntrega == 'DELIVERY') {
      final direccion = _direccionCtrl.text.trim();
      if (direccion.isEmpty) {
        setState(() => _errorPago = 'Ingresa tu dirección de entrega.');
        return;
      }
      if (_lat == null || _lng == null) {
        setState(() => _errorPago =
            'Marca tu ubicación en el mapa o toca "Usar mi ubicación" para calcular el envío.');
        return;
      }
      if (_cotizacion == null) {
        setState(() => _errorPago = 'Espera a que se calcule el costo de envío.');
        return;
      }
      entrega = {
        'direccion': direccion,
        'referencia': _referenciaCtrl.text.trim(),
        'latitud': _lat,
        'longitud': _lng,
      };
    }

    setState(() {
      _iniciandoPago = true;
      _errorPago = null;
    });
    try {
      final data = await _cartService.checkout(_sucursalSeleccionada!, entrega: entrega);
      if (!mounted) return;
      setState(() {
        _clientSecret = data['client_secret'] as String;
        _mostrarFormularioPago = true;
        _iniciandoPago = false;
      });
    } catch (e) {
      if (!mounted) return;
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
      if (!mounted) return;
      setState(() {
        _ordenConfirmada = orden;
        _mostrarFormularioPago = false;
        _confirmandoPago = false;
      });
      _cargar();
    } on StripeException catch (e) {
      if (!mounted) return;
      setState(() {
        _errorPago = e.error.localizedMessage ?? 'La tarjeta fue rechazada.';
        _confirmandoPago = false;
      });
    } catch (e) {
      if (!mounted) return;
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

  // ---- Interfaz ----

  @override
  Widget build(BuildContext context) {
    if (_ordenConfirmada != null) {
      return _pantallaConfirmacion();
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
                  child: SingleChildScrollView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        for (final item in items) _tarjetaItem(item as Map<String, dynamic>),
                        const SizedBox(height: 8),
                        _resumen(),
                        const SizedBox(height: 16),
                        if (!_mostrarFormularioPago) _seccionEntrega(),
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
                        if (_mostrarFormularioPago) _seccionPago(),
                        const SizedBox(height: 24),
                      ],
                    ),
                  ),
                ),
    );
  }

  Widget _pantallaConfirmacion() {
    final orden = _ordenConfirmada!;
    final esDelivery = orden['tipo_entrega'] == 'DELIVERY';
    final delivery = orden['delivery'] as Map?;
    return Scaffold(
      appBar: AppBar(title: const Text('Mi Carrito')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.check_circle, color: Colors.green, size: 64),
            const SizedBox(height: 16),
            const Text('¡Compra realizada con éxito!',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            Text('Orden #${orden['id_orden']} - Total Bs ${orden['total']}'),
            const SizedBox(height: 4),
            if (esDelivery)
              Text(
                'Envío a domicilio (Bs ${orden['costo_envio']}): ${delivery?['direccion'] ?? ''}',
                textAlign: TextAlign.center,
              )
            else
              Text('Retiro en sucursal: ${orden['sucursal']}', textAlign: TextAlign.center),
            const SizedBox(height: 4),
            Text('Referencia de pago (Stripe): ${orden['referencia_pago']}',
                textAlign: TextAlign.center),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () => setState(() {
                _ordenConfirmada = null;
                _reiniciarEntrega();
              }),
              child: const Text('Seguir comprando'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _tarjetaItem(Map<String, dynamic> item) {
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
  }

  Widget _filaResumen(String etiqueta, String valor, {bool grande = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(etiqueta,
              style: TextStyle(fontSize: grande ? 18 : 15, fontWeight: FontWeight.w600)),
          Text(
            valor,
            style: TextStyle(
              fontSize: grande ? 20 : 15,
              fontWeight: FontWeight.bold,
              color: grande ? AppColors.accent : null,
            ),
          ),
        ],
      ),
    );
  }

  Widget _resumen() {
    final esDelivery = _tipoEntrega == 'DELIVERY';
    return Column(
      children: [
        const Divider(),
        _filaResumen(
          esDelivery ? 'Subtotal' : 'Total',
          'Bs ${_totalProductos.toStringAsFixed(2)}',
          grande: !esDelivery,
        ),
        if (esDelivery && _cotizacion != null) ...[
          _filaResumen(
            'Envío (${_cotizacion!['distancia_km']} km)',
            'Bs ${_costoEnvio.toStringAsFixed(2)}',
          ),
          _filaResumen('Total a pagar', 'Bs ${_totalAPagar.toStringAsFixed(2)}', grande: true),
        ],
      ],
    );
  }

  Widget _seccionEntrega() {
    final esDelivery = _tipoEntrega == 'DELIVERY';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SegmentedButton<String>(
          segments: const [
            ButtonSegment<String>(
              value: 'RETIRO',
              label: Text('Retiro'),
              icon: Icon(Icons.store_outlined),
            ),
            ButtonSegment<String>(
              value: 'DELIVERY',
              label: Text('Delivery'),
              icon: Icon(Icons.delivery_dining),
            ),
          ],
          selected: {_tipoEntrega},
          onSelectionChanged: (seleccion) => _onCambioTipo(seleccion.first),
        ),
        const SizedBox(height: 12),
        DropdownButtonFormField<int>(
          value: _sucursalSeleccionada,
          decoration: InputDecoration(
            labelText: esDelivery ? 'Sucursal que despacha tu pedido' : 'Sucursal de retiro',
            border: const OutlineInputBorder(),
          ),
          items: _sucursales
              .map((s) => DropdownMenuItem<int>(
                    value: s['id_sucursal'] as int,
                    child: Text(s['nombre'].toString()),
                  ))
              .toList(),
          onChanged: _onCambioSucursal,
        ),
        if (esDelivery) ...[
          const SizedBox(height: 12),
          TextField(
            controller: _direccionCtrl,
            maxLength: 250,
            maxLines: 2,
            minLines: 1,
            decoration: const InputDecoration(
              labelText: 'Dirección de entrega',
              border: OutlineInputBorder(),
              counterText: '',
            ),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _referenciaCtrl,
            maxLength: 250,
            decoration: const InputDecoration(
              labelText: 'Referencia (opcional)',
              border: OutlineInputBorder(),
              counterText: '',
            ),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: (_ubicando || _cotizando) ? null : _usarMiUbicacion,
            icon: const Icon(Icons.my_location),
            label: Text(_ubicando
                ? 'Obteniendo ubicación...'
                : (_lat != null ? 'Actualizar mi ubicación' : 'Usar mi ubicación')),
          ),
          const SizedBox(height: 12),
          _mapa(),
          const SizedBox(height: 4),
          const Text(
            'Toca el mapa para indicar dónde entregamos tu pedido.',
            style: TextStyle(fontSize: 12, color: AppColors.grey),
          ),
          if (_cotizando) ...[
            const SizedBox(height: 8),
            const Text('Calculando el costo de envío...', style: TextStyle(fontSize: 13)),
          ],
          if (_cotizacion != null && !_cotizando) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFFEEF3FB),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Distancia: ${_cotizacion!['distancia_km']} km '
                    '(${_cotizacion!['fuente_distancia'] == 'openrouteservice' ? 'ruta real por calles' : 'distancia aproximada'})',
                  ),
                  const SizedBox(height: 2),
                  Text(
                    'Costo de envío: Bs ${_costoEnvio.toStringAsFixed(2)}',
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                ],
              ),
            ),
          ],
        ],
      ],
    );
  }

  Widget _mapa() {
    final cliente = _puntoCliente;
    final sucursal = _puntoSucursal;
    return ClipRRect(
      borderRadius: BorderRadius.circular(8),
      child: SizedBox(
        height: 280,
        child: FlutterMap(
          mapController: _mapController,
          options: MapOptions(
            initialCenter: cliente ?? sucursal ?? _centroDefecto,
            initialZoom: cliente != null ? 16 : 14,
            onTap: (tapPosition, punto) => _marcarPunto(punto),
          ),
          children: [
            TileLayer(
              urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
              userAgentPackageName: 'com.example.smartlook_mobile',
            ),
            MarkerLayer(
              markers: [
                if (sucursal != null)
                  Marker(
                    point: sucursal,
                    width: 36,
                    height: 36,
                    child: const Icon(Icons.store, color: Color(0xFFE94560), size: 32),
                  ),
                if (cliente != null)
                  Marker(
                    point: cliente,
                    width: 40,
                    height: 40,
                    alignment: Alignment.topCenter,
                    child: const Icon(Icons.location_on, color: Color(0xFF0F3460), size: 40),
                  ),
              ],
            ),
            RichAttributionWidget(
              attributions: [
                TextSourceAttribution('© OpenStreetMap contributors'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  // Paso 2: campo de tarjeta real (SDK de Stripe)
  Widget _seccionPago() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
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
          child: Text(_confirmandoPago
              ? 'Procesando pago...'
              : 'Pagar Bs ${_totalAPagar.toStringAsFixed(2)}'),
        ),
        TextButton(
          onPressed: _confirmandoPago ? null : _cancelarPago,
          child: const Text('Cancelar'),
        ),
      ],
    );
  }
}
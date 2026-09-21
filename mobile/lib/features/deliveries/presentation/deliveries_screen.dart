// mobile/lib/features/deliveries/presentation/deliveries_screen.dart

import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/network/api_client.dart';
import '../../../core/services/auth_service.dart';
import '../../../shared/theme/app_colors.dart';

class DeliveriesScreen extends StatefulWidget {
  /// true cuando es la pantalla inicial del repartidor (sin botón de volver
  /// y con "Cerrar sesión").
  final bool esInicio;

  const DeliveriesScreen({super.key, this.esInicio = false});

  @override
  State<DeliveriesScreen> createState() => _DeliveriesScreenState();
}

class _DeliveriesScreenState extends State<DeliveriesScreen> {
  late final ApiClient _api;
  late final bool _esGestor;

  List<Map<String, dynamic>> _entregas = [];
  List<Map<String, dynamic>> _repartidores = [];
  final Map<int, int?> _seleccion = {};
  bool _cargando = true;
  int? _procesando;
  String _filtro = '';
  Timer? _timer;

  static const List<List<String>> _filtros = [
    ['', 'Todas'],
    ['PENDIENTE', 'Pendientes'],
    ['EN_PREPARACION', 'En preparación'],
    ['EN_CAMINO', 'En camino'],
    ['ENTREGADO', 'Entregadas'],
  ];

  @override
  void initState() {
    super.initState();
    _api = context.read<ApiClient>();
    final usuario = context.read<AuthService>().currentUser;
    _esGestor = usuario != null &&
        (usuario.hasRole('SUPER_ADMIN') ||
            usuario.hasRole('ADMIN_EMPRESA') ||
            usuario.hasRole('ENCARGADO_SUCURSAL'));
    if (_esGestor) _cargarRepartidores();
    _cargar();
    _timer = Timer.periodic(const Duration(seconds: 10), (_) => _cargar());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  String _errorDe(Object e, String fallback) {
    try {
      final data = (e as dynamic).response?.data;
      if (data is Map) {
        if (data['error'] != null) return data['error'].toString();
        if (data['detail'] != null) return data['detail'].toString();
      }
    } catch (_) {}
    return fallback;
  }

  void _avisar(String texto, {bool error = false}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(texto),
        backgroundColor: error ? AppColors.danger : null,
      ),
    );
  }

  Future<void> _cargarRepartidores() async {
    try {
      final response = await _api.dio.get('/sales/entregas/repartidores/');
      final lista = (response.data as List)
          .map((e) => Map<String, dynamic>.from(e as Map))
          .toList();
      if (!mounted) return;
      setState(() => _repartidores = lista);
    } catch (_) {
      if (!mounted) return;
      setState(() => _repartidores = []);
    }
  }

  Future<void> _cargar() async {
    try {
      final response = await _api.dio.get(
        '/sales/entregas/',
        queryParameters: {
          'page_size': 100,
          if (_filtro.isNotEmpty) 'estado': _filtro,
        },
      );
      final data = response.data;
      final lista = (data is Map ? (data['results'] ?? []) : data) as List;
      if (!mounted) return;
      setState(() {
        _entregas = lista.map((e) => Map<String, dynamic>.from(e as Map)).toList();
        _cargando = false;
        // Deja preseleccionado el repartidor ya asignado, sin pisar lo que el usuario esté eligiendo.
        for (final d in _entregas) {
          final id = d['id_delivery'] as int;
          if (d['id_repartidor'] != null && _seleccion[id] == null) {
            _seleccion[id] = d['id_repartidor'] as int;
          }
        }
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _cargando = false);
    }
  }

  void _cambiarFiltro(String valor) {
    setState(() {
      _filtro = valor;
      _cargando = true;
    });
    _cargar();
  }

  Future<void> _ejecutar(Map<String, dynamic> d, String accion, {Map<String, dynamic>? body}) async {
    final id = d['id_delivery'] as int;
    setState(() => _procesando = id);
    try {
      await _api.dio.post('/sales/entregas/$id/$accion/', data: body ?? {});
      if (!mounted) return;
      setState(() => _procesando = null);
      _avisar('Entrega #$id actualizada.');
      _cargar();
    } catch (e) {
      if (!mounted) return;
      setState(() => _procesando = null);
      _avisar(_errorDe(e, 'No se pudo completar la acción.'), error: true);
    }
  }

  void _asignar(Map<String, dynamic> d) {
    final elegido = _valorSeleccion(d);
    if (elegido == null) {
      _avisar('Elige un repartidor antes de asignar.', error: true);
      return;
    }
    _ejecutar(d, 'asignar', body: {'id_repartidor': elegido});
  }

  // Solo devuelve un valor que exista en la lista, para que el desplegable no falle.
  int? _valorSeleccion(Map<String, dynamic> d) {
    final v = _seleccion[d['id_delivery'] as int];
    return _repartidores.any((r) => r['id_usuario'] == v) ? v : null;
  }

  // Abre el mapa (Google Maps o el navegador) con la ruta hasta el punto de entrega.
  Future<void> _abrirMapa(Map<String, dynamic> d) async {
    final uri = Uri.parse(
      'https://www.google.com/maps/dir/?api=1&destination=${d['latitud']},${d['longitud']}&travelmode=driving',
    );
    try {
      final abierto = await launchUrl(uri, mode: LaunchMode.externalApplication);
      if (!abierto) _avisar('No se pudo abrir el mapa.', error: true);
    } catch (_) {
      _avisar('No se pudo abrir el mapa.', error: true);
    }
  }

  Future<void> _cerrarSesion() async {
    final nav = Navigator.of(context);
    await context.read<AuthService>().logout();
    nav.pushNamedAndRemoveUntil('/login', (_) => false);
  }

  String _textoEstado(String estado) {
    switch (estado) {
      case 'PENDIENTE':
        return 'Pendiente';
      case 'EN_PREPARACION':
        return 'En preparación';
      case 'EN_CAMINO':
        return 'En camino';
      case 'ENTREGADO':
        return 'Entregado';
      default:
        return estado;
    }
  }

  Color _colorEstado(String estado) {
    switch (estado) {
      case 'EN_PREPARACION':
        return const Color(0xFFB26A00);
      case 'EN_CAMINO':
        return const Color(0xFF1565C0);
      case 'ENTREGADO':
        return const Color(0xFF1B7F4B);
      default:
        return AppColors.primary;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_esGestor ? 'Entregas' : 'Mis entregas'),
        automaticallyImplyLeading: !widget.esInicio,
        actions: [
          if (widget.esInicio)
            IconButton(
              icon: const Icon(Icons.logout),
              tooltip: 'Cerrar sesión',
              onPressed: _cerrarSesion,
            ),
        ],
      ),
      body: Column(
        children: [
          SizedBox(
            height: 56,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              children: [
                for (final f in _filtros)
                  Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      label: Text(f[1]),
                      selected: _filtro == f[0],
                      onSelected: (_) => _cambiarFiltro(f[0]),
                    ),
                  ),
              ],
            ),
          ),
          Expanded(
            child: _cargando
                ? const Center(child: CircularProgressIndicator())
                : RefreshIndicator(
                    onRefresh: _cargar,
                    child: _entregas.isEmpty
                        ? ListView(
                            children: const [
                              SizedBox(height: 100),
                              Center(
                                child: Text(
                                  'No hay entregas en esta lista.',
                                  style: TextStyle(color: AppColors.grey),
                                ),
                              ),
                            ],
                          )
                        : ListView.builder(
                            padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
                            itemCount: _entregas.length,
                            itemBuilder: (context, i) => _tarjeta(_entregas[i]),
                          ),
                  ),
          ),
        ],
      ),
    );
  }

  Widget _tarjeta(Map<String, dynamic> d) {
    final estado = d['estado'] as String;
    final color = _colorEstado(estado);
    final referencia = (d['referencia'] ?? '').toString();
    final telefono = (d['telefono_cliente'] ?? '').toString();

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Entrega #${d['id_delivery']}',
                          style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
                      Text('Orden #${d['orden']} · ${d['sucursal']}',
                          style: const TextStyle(color: AppColors.grey, fontSize: 12)),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(
                    _textoEstado(estado),
                    style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.w700),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text('Cliente: ${d['cliente']}${telefono.isNotEmpty ? ' · Tel. $telefono' : ''}'),
            const SizedBox(height: 2),
            Text('Dirección: ${d['direccion']}${referencia.isNotEmpty ? ' ($referencia)' : ''}'),
            const SizedBox(height: 2),
            Text(
              '${d['prendas']} prenda(s) · ${d['distancia_km']} km · Pagado Bs ${d['total_orden']}',
              style: const TextStyle(color: AppColors.grey, fontSize: 12),
            ),
            const SizedBox(height: 2),
            Text('Repartidor: ${d['repartidor'] ?? 'Sin asignar'}'),
            TextButton.icon(
              style: TextButton.styleFrom(
                padding: EdgeInsets.zero,
                alignment: Alignment.centerLeft,
              ),
              onPressed: () => _abrirMapa(d),
              icon: const Icon(Icons.directions, size: 20),
              label: const Text('Cómo llegar'),
            ),
            _acciones(d),
          ],
        ),
      ),
    );
  }

  Widget _acciones(Map<String, dynamic> d) {
    final id = d['id_delivery'] as int;
    final estado = d['estado'] as String;
    final ocupado = _procesando == id;
    final widgets = <Widget>[];

    if (_esGestor && (estado == 'PENDIENTE' || estado == 'EN_PREPARACION')) {
      widgets.add(SizedBox(
        width: 180,
        child: DropdownButton<int>(
          isExpanded: true,
          isDense: true,
          value: _valorSeleccion(d),
          hint: const Text('Repartidor'),
          items: _repartidores
              .map((r) => DropdownMenuItem<int>(
                    value: r['id_usuario'] as int,
                    child: Text('${r['nombre']}', overflow: TextOverflow.ellipsis),
                  ))
              .toList(),
          onChanged: (v) => setState(() => _seleccion[id] = v),
        ),
      ));
      widgets.add(OutlinedButton(
        onPressed: ocupado ? null : () => _asignar(d),
        child: const Text('Asignar'),
      ));
    }

    if (_esGestor && estado == 'PENDIENTE') {
      widgets.add(ElevatedButton(
        onPressed: ocupado ? null : () => _ejecutar(d, 'preparar'),
        child: const Text('Preparar pedido'),
      ));
    }

    if (estado == 'EN_PREPARACION') {
      widgets.add(ElevatedButton(
        onPressed: (ocupado || d['id_repartidor'] == null)
            ? null
            : () => _ejecutar(d, 'en-camino'),
        child: const Text('Salir a entregar'),
      ));
    }

    if (estado == 'EN_CAMINO') {
      widgets.add(ElevatedButton(
        onPressed: ocupado ? null : () => _ejecutar(d, 'entregar'),
        child: const Text('Marcar entregado'),
      ));
    }

    if (widgets.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(top: 10),
      child: Wrap(
        spacing: 8,
        runSpacing: 8,
        crossAxisAlignment: WrapCrossAlignment.center,
        children: widgets,
      ),
    );
  }
}
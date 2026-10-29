// mobile/lib/features/client/presentation/profile_screen.dart
//
// NUEVO: perfil del cliente (igual que en la web).
// - Datos: nombres, apellidos, teléfono y dirección editables con
//   PATCH /auth/perfil/. El correo no, porque es el usuario de inicio de sesión.
// - Historial de compras: pedidos del cliente en todas las tiendas
//   (GET /sales/ordenes/), sin los PENDIENTE (pagos que no se completaron).
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../../../core/network/api_client.dart';
import '../../../core/services/auth_service.dart';
import '../../../shared/theme/app_colors.dart';

final RegExp _patronTelefono = RegExp(r'^(\+?591)?\s?[67]\d{7}$');

class ProfileScreen extends StatefulWidget {
  /// Lleva a la pestaña "Pedidos" del inicio del cliente.
  final VoidCallback? onVerPedidos;

  const ProfileScreen({super.key, this.onVerPedidos});

  @override
  State<ProfileScreen> createState() => ProfileScreenState();
}

class ProfileScreenState extends State<ProfileScreen> {
  late final ApiClient _api;
  final _formKey = GlobalKey<FormState>();
  final _nombresCtrl = TextEditingController();
  final _apellidosCtrl = TextEditingController();
  final _telefonoCtrl = TextEditingController();
  final _direccionCtrl = TextEditingController();

  Map<String, dynamic>? _perfil;
  List<Map<String, dynamic>> _compras = [];
  bool _cargando = true;
  bool _cargandoCompras = false;
  bool _guardando = false;
  String? _errorCarga;
  String? _errorGuardar;
  String? _mensajeOk;

  final DateFormat _fmtFecha = DateFormat('dd/MM/yyyy');
  final DateFormat _fmtFechaHora = DateFormat('dd/MM/yyyy HH:mm');

  @override
  void initState() {
    super.initState();
    _api = context.read<ApiClient>();
    recargar();
  }

  @override
  void dispose() {
    _nombresCtrl.dispose();
    _apellidosCtrl.dispose();
    _telefonoCtrl.dispose();
    _direccionCtrl.dispose();
    super.dispose();
  }

  /// Vuelve a pedir perfil e historial (al abrir la pestaña o deslizar).
  Future<void> recargar() async {
    setState(() {
      _cargando = _perfil == null;
      _errorCarga = null;
    });
    try {
      final response = await _api.dio.get('/auth/perfil/');
      if (!mounted) return;
      final perfil = Map<String, dynamic>.from(response.data as Map);
      setState(() {
        _cargando = false;
        _mostrarPerfil(perfil);
      });
      if (perfil['es_cliente'] == true) {
        await _cargarCompras();
      }
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _cargando = false;
        if (_perfil == null) _errorCarga = 'No se pudo cargar tu perfil.';
      });
    }
  }

  void _mostrarPerfil(Map<String, dynamic> perfil) {
    _perfil = perfil;
    _nombresCtrl.text = perfil['nombres']?.toString() ?? '';
    _apellidosCtrl.text = perfil['apellidos']?.toString() ?? '';
    _telefonoCtrl.text = perfil['telefono']?.toString() ?? '';
    _direccionCtrl.text = perfil['direccion']?.toString() ?? '';
  }

  Future<void> _cargarCompras() async {
    setState(() => _cargandoCompras = true);
    try {
      final response = await _api.dio.get(
        '/sales/ordenes/',
        queryParameters: {'page_size': 100},
      );
      final data = response.data;
      final lista = (data is Map ? (data['results'] ?? []) : data) as List;
      if (!mounted) return;
      setState(() {
        _compras = lista
            .map((e) => Map<String, dynamic>.from(e as Map))
            .where((o) => o['estado'] != 'PENDIENTE')
            .toList();
        _cargandoCompras = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _compras = [];
        _cargandoCompras = false;
      });
    }
  }

  // ---- Datos derivados ----

  String get _iniciales {
    final n = (_perfil?['nombres']?.toString() ?? '');
    final a = (_perfil?['apellidos']?.toString() ?? '');
    return ((n.isNotEmpty ? n[0] : '') + (a.isNotEmpty ? a[0] : '')).toUpperCase();
  }

  /// Suma de lo comprado, sin contar pedidos cancelados.
  double get _totalGastado => _compras
      .where((o) => o['estado'] != 'CANCELADA')
      .fold<double>(0, (suma, o) => suma + (double.tryParse('${o['total']}') ?? 0));

  int _prendas(Map<String, dynamic> orden) {
    final items = (orden['items'] ?? []) as List;
    return items.fold<int>(0, (suma, i) => suma + (int.tryParse('${i['cantidad']}') ?? 0));
  }

  String _textoEstado(Map<String, dynamic> orden) {
    if (orden['estado'] == 'CANCELADA') return 'Cancelado';
    if (orden['devuelto'] == true) return 'Devuelto';
    return orden['estado'] == 'ENTREGADA' ? 'Entregado' : 'Pagado';
  }

  String _fecha(dynamic valor, DateFormat formato) {
    final fecha = DateTime.tryParse('${valor ?? ''}');
    return fecha == null ? '' : formato.format(fecha.toLocal());
  }

  // ---- Guardar ----

  Future<void> _guardar() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    final esCliente = _perfil?['es_cliente'] == true;
    final telefono = _telefonoCtrl.text.trim();
    final datos = <String, dynamic>{
      'nombres': _nombresCtrl.text.trim(),
      'apellidos': _apellidosCtrl.text.trim(),
      'telefono': telefono.isEmpty ? null : telefono,
    };
    if (esCliente) {
      final direccion = _direccionCtrl.text.trim();
      datos['direccion'] = direccion.isEmpty ? null : direccion;
    }
    setState(() {
      _guardando = true;
      _errorGuardar = null;
      _mensajeOk = null;
    });
    try {
      final response = await _api.dio.patch('/auth/perfil/', data: datos);
      if (!mounted) return;
      final perfil = Map<String, dynamic>.from(response.data as Map);
      await context.read<AuthService>().actualizarDatosLocales(
            nombres: perfil['nombres']?.toString() ?? '',
            apellidos: perfil['apellidos']?.toString() ?? '',
            telefono: perfil['telefono']?.toString(),
          );
      if (!mounted) return;
      setState(() {
        _guardando = false;
        _mostrarPerfil(perfil);
        _mensajeOk = 'Datos guardados.';
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _guardando = false;
        _errorGuardar = _extraerError(e);
      });
    }
  }

  String _extraerError(Object e) {
    if (e is DioException && e.response?.data is Map) {
      final data = e.response!.data as Map;
      for (final campo in ['telefono', 'nombres', 'apellidos', 'direccion']) {
        final valor = data[campo];
        if (valor is List && valor.isNotEmpty) return valor.first.toString();
        if (valor is String && valor.isNotEmpty) return valor;
      }
      if (data['detail'] != null) return data['detail'].toString();
    }
    return 'No se pudieron guardar los cambios.';
  }

  // ---- Interfaz ----

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mi perfil')),
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : _perfil == null
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(_errorCarga ?? 'No se pudo cargar tu perfil.',
                          style: const TextStyle(color: AppColors.danger)),
                      const SizedBox(height: 12),
                      OutlinedButton(onPressed: recargar, child: const Text('Reintentar')),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: recargar,
                  child: ListView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(16),
                    children: [
                      _tarjetaDatos(),
                      if (_perfil!['es_cliente'] == true) ...[
                        const SizedBox(height: 16),
                        _tarjetaHistorial(),
                      ],
                      const SizedBox(height: 24),
                    ],
                  ),
                ),
    );
  }

  Widget _tarjetaDatos() {
    final esCliente = _perfil!['es_cliente'] == true;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  CircleAvatar(
                    radius: 34,
                    backgroundColor: AppColors.primary,
                    child: Text(
                      _iniciales,
                      style: const TextStyle(
                        color: AppColors.white,
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${_perfil!['nombres'] ?? ''} ${_perfil!['apellidos'] ?? ''}',
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: AppColors.primary,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text('${_perfil!['correo'] ?? ''}'),
                        if (esCliente && _perfil!['fecha_registro'] != null)
                          Text(
                            'Cliente desde ${_fecha(_perfil!['fecha_registro'], _fmtFecha)}',
                            style: const TextStyle(fontSize: 12, color: AppColors.grey),
                          ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              TextFormField(
                controller: _nombresCtrl,
                maxLength: 100,
                decoration: const InputDecoration(
                  labelText: 'Nombres',
                  border: OutlineInputBorder(),
                  counterText: '',
                ),
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? 'Los nombres son obligatorios.' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _apellidosCtrl,
                maxLength: 100,
                decoration: const InputDecoration(
                  labelText: 'Apellidos',
                  border: OutlineInputBorder(),
                  counterText: '',
                ),
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? 'Los apellidos son obligatorios.' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                initialValue: _perfil!['correo']?.toString() ?? '',
                enabled: false,
                decoration: const InputDecoration(
                  labelText: 'Correo',
                  border: OutlineInputBorder(),
                  helperText: 'El correo es tu usuario de inicio de sesión y no se puede cambiar.',
                  helperMaxLines: 2,
                ),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _telefonoCtrl,
                maxLength: 20,
                keyboardType: TextInputType.phone,
                decoration: const InputDecoration(
                  labelText: 'Teléfono',
                  border: OutlineInputBorder(),
                  counterText: '',
                ),
                validator: (v) {
                  final t = (v ?? '').trim();
                  if (t.isEmpty) return null;
                  return _patronTelefono.hasMatch(t)
                      ? null
                      : 'Debe tener 8 dígitos y comenzar con 6 o 7.';
                },
              ),
              if (esCliente) ...[
                const SizedBox(height: 12),
                TextFormField(
                  controller: _direccionCtrl,
                  maxLength: 250,
                  decoration: const InputDecoration(
                    labelText: 'Dirección',
                    border: OutlineInputBorder(),
                    counterText: '',
                  ),
                ),
              ],
              if (_mensajeOk != null) ...[
                const SizedBox(height: 12),
                Text(_mensajeOk!, style: const TextStyle(color: AppColors.success)),
              ],
              if (_errorGuardar != null) ...[
                const SizedBox(height: 12),
                Text(_errorGuardar!, style: const TextStyle(color: AppColors.danger)),
              ],
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _guardando ? null : _guardar,
                style: ElevatedButton.styleFrom(minimumSize: const Size(double.infinity, 48)),
                child: Text(_guardando ? 'Guardando...' : 'Guardar cambios'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _tarjetaHistorial() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                const Expanded(
                  child: Text(
                    'Historial de compras',
                    style: TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.bold,
                      color: AppColors.primary,
                    ),
                  ),
                ),
                if (widget.onVerPedidos != null)
                  TextButton(
                    onPressed: widget.onVerPedidos,
                    child: const Text('Ver mis pedidos'),
                  ),
              ],
            ),
            if (_compras.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(
                  '${_compras.length} compra(s) · Total Bs ${_totalGastado.toStringAsFixed(2)}',
                  style: const TextStyle(
                    color: AppColors.accent,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            if (_cargandoCompras && _compras.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 12),
                child: Text('Cargando compras...'),
              )
            else if (_compras.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 12),
                child: Text(
                  'Todavía no tienes compras.',
                  style: TextStyle(color: AppColors.grey),
                ),
              )
            else
              for (final o in _compras) _filaCompra(o),
          ],
        ),
      ),
    );
  }

  Widget _filaCompra(Map<String, dynamic> o) {
    final empresa = o['empresa_nombre']?.toString() ?? '';
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 10),
      decoration: const BoxDecoration(
        border: Border(top: BorderSide(color: Color(0xFFEEEEEE))),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  'Pedido #${o['id_orden']}',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                decoration: BoxDecoration(
                  color: const Color(0xFFEEF3FB),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(
                  _textoEstado(o),
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: AppColors.accent,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Wrap(
            spacing: 12,
            runSpacing: 2,
            children: [
              Text(_fecha(o['fecha_creacion'], _fmtFechaHora),
                  style: const TextStyle(fontSize: 13, color: AppColors.grey)),
              if (empresa.isNotEmpty)
                Text('Tienda: $empresa',
                    style: const TextStyle(fontSize: 13, color: AppColors.grey)),
              Text('${_prendas(o)} prenda(s)',
                  style: const TextStyle(fontSize: 13, color: AppColors.grey)),
            ],
          ),
          const SizedBox(height: 2),
          Align(
            alignment: Alignment.centerRight,
            child: Text(
              'Bs ${o['total']}',
              style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.dark),
            ),
          ),
        ],
      ),
    );
  }
}
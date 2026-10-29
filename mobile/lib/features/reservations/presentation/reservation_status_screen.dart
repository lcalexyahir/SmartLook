// mobile/lib/features/reservations/presentation/reservation_status_screen.dart
//
// Lista las reservas del cliente (el backend filtra por el usuario) y permite
// cancelar las que estén PENDIENTE o CONFIRMADA.
// MODIFICADO (SaaS - 6.2): el cliente ve también sus reservas hechas sin
// conexión con su estado (Registrada localmente, Enviada, Confirmada,
// Rechazada), puede sincronizarlas, descartar las rechazadas y quitar las
// confirmadas. Sin conexión, la lista del servidor sale de la copia guardada.
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../../../core/network/api_client.dart';
import '../../../shared/theme/app_colors.dart';
import '../data/reservation_service.dart';
import '../data/reserva_offline_service.dart';
import 'reservation_form_screen.dart';

class ReservationStatusScreen extends StatefulWidget {
  const ReservationStatusScreen({super.key});

  @override
  State<ReservationStatusScreen> createState() => _ReservationStatusScreenState();
}

class _ReservationStatusScreenState extends State<ReservationStatusScreen> {
  static const Color _naranja = Color(0xFFE65100);
  static const Color _fondoNaranja = Color(0xFFFFF3E0);

  late final ReservationService _reservationService;
  late final ReservaOfflineService _offline;
  final DateFormat _fmt = DateFormat('dd/MM/yyyy HH:mm');

  List<dynamic> _reservas = [];
  bool _loading = true;
  bool _sinDatosGuardados = false;
  DateTime? _fechaCopia;
  ResultadoSyncReservas? _ultimoResultado;

  @override
  void initState() {
    super.initState();
    _reservationService = ReservationService(apiClient: context.read<ApiClient>());
    _offline = context.read<ReservaOfflineService>();
    _ultimoResultado = _offline.resultado;
    _offline.addListener(_alCambiarOffline);
    _offline.recargar();
    _offline.sincronizar();
    _cargar();
  }

  @override
  void dispose() {
    _offline.removeListener(_alCambiarOffline);
    super.dispose();
  }

  // Las reservas confirmadas en una sincronización ya aparecen en la lista del servidor.
  void _alCambiarOffline() {
    final r = _offline.resultado;
    if (r != null && r != _ultimoResultado && r.sincronizadas + r.duplicadas > 0) {
      _ultimoResultado = r;
      _cargar();
    } else {
      _ultimoResultado = r;
    }
  }

  Future<void> _cargar() async {
    setState(() {
      _loading = true;
      _sinDatosGuardados = false;
    });
    try {
      final reservas = await _reservationService.getReservas();
      _offline.guardarMisReservas(reservas);
      if (!mounted) return;
      setState(() {
        _reservas = reservas;
        _fechaCopia = null;
        _loading = false;
      });
    } catch (e) {
      if (_offline.esErrorDeRedApi(e)) {
        _offline.marcarSinConexion();
        final copia = await _offline.misReservasLocales();
        if (!mounted) return;
        setState(() {
          _loading = false;
          if (copia != null) {
            _reservas = copia.$1;
            _fechaCopia = copia.$2;
          } else {
            _sinDatosGuardados = true;
          }
        });
        return;
      }
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _cancelar(int id) async {
    try {
      await _reservationService.cancelarReserva(id);
      _cargar();
    } catch (e) {
      if (!mounted) return;
      final mensaje = _offline.esErrorDeRedApi(e)
          ? 'Sin conexión: la reserva no se puede cancelar ahora. Inténtalo al recuperar internet.'
          : 'No se pudo cancelar la reserva.';
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(mensaje)));
    }
  }

  Future<void> _descartar(ReservaLocal reserva) async {
    final confirmar = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        content: const Text('¿Descartar esta reserva rechazada? Se borrará de este dispositivo.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Descartar', style: TextStyle(color: AppColors.danger)),
          ),
        ],
      ),
    );
    if (confirmar == true) await _offline.descartar(reserva);
  }

  Color _colorEstado(String estado) {
    switch (estado) {
      case 'PENDIENTE':
        return Colors.orange;
      case 'CONFIRMADA':
        return Colors.blue;
      case 'COMPLETADA':
        return AppColors.success;
      case 'CANCELADA':
        return AppColors.danger;
      default:
        return AppColors.grey;
    }
  }

  bool _puedeCancelar(String estado) => estado == 'PENDIENTE' || estado == 'CONFIRMADA';

  String _textoEstadoLocal(ReservaLocal r) {
    switch (r.estado) {
      case EstadoReservaLocal.confirmada:
        return r.idReserva != null ? 'Confirmada · Reserva #${r.idReserva}' : 'Confirmada';
      case EstadoReservaLocal.rechazada:
        return 'Rechazada';
      case EstadoReservaLocal.enviada:
        return 'Enviada';
      default:
        return 'Registrada localmente';
    }
  }

  (Color, Color) _coloresLocal(String estado) {
    switch (estado) {
      case EstadoReservaLocal.enviada:
        return (const Color(0xFFE3F2FD), const Color(0xFF0D47A1));
      case EstadoReservaLocal.confirmada:
        return (const Color(0xFFE8F5E9), const Color(0xFF1B5E20));
      case EstadoReservaLocal.rechazada:
        return (const Color(0xFFFDECEA), const Color(0xFFC0392B));
      default:
        return (_fondoNaranja, _naranja);
    }
  }

  @override
  Widget build(BuildContext context) {
    final offline = context.watch<ReservaOfflineService>();
    final mostrarCola = offline.reservas.isNotEmpty || offline.resultado != null;
    return Scaffold(
      appBar: AppBar(title: const Text('Mis Reservas')),
      body: RefreshIndicator(
        onRefresh: () async {
          await offline.sincronizar();
          await _cargar();
        },
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
          children: [
            if (mostrarCola) ...[
              _seccionCola(offline),
              const SizedBox(height: 16),
            ],
            if (_fechaCopia != null)
              Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(color: _fondoNaranja, borderRadius: BorderRadius.circular(6)),
                child: Text(
                  'Sin conexión: lista guardada el ${_fmt.format(_fechaCopia!.toLocal())}. Puede estar desactualizada.',
                  style: const TextStyle(fontSize: 13, color: Color(0xFF8A4B00)),
                ),
              ),
            if (_loading)
              const Padding(
                padding: EdgeInsets.all(24),
                child: Center(child: CircularProgressIndicator()),
              )
            else if (_sinDatosGuardados)
              const Padding(
                padding: EdgeInsets.all(24),
                child: Text(
                  'Sin conexión y sin reservas guardadas en este dispositivo. Se mostrarán al recuperar internet.',
                  textAlign: TextAlign.center,
                ),
              )
            else if (_reservas.isEmpty)
              const Padding(
                padding: EdgeInsets.all(24),
                child: Center(child: Text('Todavía no tienes reservas.')),
              )
            else
              ..._reservas.map((r) => _tarjetaServidor(r as Map)),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          await Navigator.push(
            context,
            MaterialPageRoute(builder: (context) => const ReservationFormScreen()),
          );
          _offline.recargar();
          _cargar();
        },
        icon: const Icon(Icons.add),
        label: const Text('Nueva Reserva'),
      ),
    );
  }

  Widget _tarjetaServidor(Map reserva) {
    final items = (reserva['items'] ?? []) as List<dynamic>;
    final estado = reserva['estado'].toString();
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    reserva['sucursal']?.toString() ?? '',
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: _colorEstado(estado).withOpacity(0.15),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    estado,
                    style: TextStyle(
                      color: _colorEstado(estado),
                      fontWeight: FontWeight.w600,
                      fontSize: 12,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text('${reserva['fecha_reserva']} - ${reserva['hora_reserva']}'),
            const SizedBox(height: 6),
            ...items.map((item) => Text('• ${item['variante']}')),
            if (_puedeCancelar(estado) && _fechaCopia == null) ...[
              const SizedBox(height: 8),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton(
                  onPressed: () => _cancelar(reserva['id_reserva'] as int),
                  child: const Text('Cancelar', style: TextStyle(color: AppColors.danger)),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _seccionCola(ReservaOfflineService offline) {
    final r = offline.resultado;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('Reservas sin conexión',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 4,
              children: [
                if (offline.confirmadas > 0)
                  OutlinedButton(
                    onPressed: offline.limpiarConfirmadas,
                    child: const Text('Quitar confirmadas'),
                  ),
                OutlinedButton(
                  onPressed: (!offline.enLinea || offline.sincronizando || offline.pendientes == 0)
                      ? null
                      : offline.sincronizar,
                  child: Text(offline.sincronizando ? 'Sincronizando...' : 'Sincronizar ahora'),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              '${offline.pendientes} por enviar · ${offline.confirmadas} confirmada(s)'
              '${offline.rechazadas > 0 ? ' · ${offline.rechazadas} rechazada(s)' : ''}',
              style: const TextStyle(fontSize: 13, color: AppColors.grey),
            ),
            if (r != null) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: r.error != null ? const Color(0xFFFDECEA) : const Color(0xFFE8F5E9),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  r.error ??
                      'Última sincronización (${DateFormat('dd/MM HH:mm').format(r.fecha.toLocal())}): '
                          '${r.sincronizadas} registrada(s), ${r.duplicadas} ya registrada(s) antes, '
                          '${r.rechazadas} rechazada(s).',
                  style: TextStyle(
                    fontSize: 13,
                    color: r.error != null ? const Color(0xFF8E2A20) : const Color(0xFF1B5E20),
                  ),
                ),
              ),
            ],
            for (final reserva in offline.reservas) _filaLocal(reserva),
          ],
        ),
      ),
    );
  }

  Widget _filaLocal(ReservaLocal r) {
    final (fondo, texto) = _coloresLocal(r.estado);
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 10),
      decoration: const BoxDecoration(
        border: Border(top: BorderSide(color: Color(0xFFF0F0F0))),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(r.sucursal.isNotEmpty ? r.sucursal : 'Sucursal',
                    style: const TextStyle(fontWeight: FontWeight.bold)),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                decoration: BoxDecoration(color: fondo, borderRadius: BorderRadius.circular(999)),
                child: Text(
                  _textoEstadoLocal(r),
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: texto),
                ),
              ),
            ],
          ),
          const SizedBox(height: 2),
          Text('Para el ${r.fechaReserva} a las ${r.horaReserva} · ${r.items.length} prenda(s)',
              style: const TextStyle(fontSize: 13, color: Color(0xFF555555))),
          Text(r.items.map((i) => i.label).join(', '),
              style: const TextStyle(fontSize: 13, color: Color(0xFF555555))),
          Text('Registrada el ${_fmt.format(r.fechaOperacion.toLocal())}',
              style: const TextStyle(fontSize: 13, color: Color(0xFF555555))),
          Text('Código: ${r.uuid}',
              style: const TextStyle(fontSize: 11, fontFamily: 'monospace', color: Color(0xFF999999))),
          if (r.estado == EstadoReservaLocal.confirmada && r.fechaConfirmacion != null)
            Text(
              'Confirmada el ${_fmt.format(r.fechaConfirmacion!.toLocal())}'
              '${r.mensaje != null ? ' · ${r.mensaje}' : ''}',
              style: const TextStyle(fontSize: 13, color: Color(0xFF1B5E20)),
            ),
          if (r.estado == EstadoReservaLocal.rechazada) ...[
            Text('Motivo: ${r.mensaje ?? ''}',
                style: const TextStyle(fontSize: 13, color: Color(0xFFC0392B))),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                onPressed: () => _descartar(r),
                child: const Text('Descartar', style: TextStyle(color: AppColors.danger)),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
// mobile/lib/features/reservations/data/reserva_offline_service.dart
//
// NUEVO (SaaS - 6.2/6.3/6.4): reservas de prendas hechas sin conexión
// (cliente), igual que la web.
// - Cola local (SQLite: reservas_local + reserva_items_local). Cada reserva
//   lleva un UUID propio, su tienda, sucursal y la hora en que se hizo.
// - Estados: REGISTRADA, ENVIADA, CONFIRMADA, RECHAZADA. Una reserva nunca se
//   borra por haberse intentado enviar; si el envío falla vuelve a REGISTRADA.
// - Subconjunto del catálogo (productos_local + variantes_producto_local) y
//   sucursales guardados para reservar sin conexión, con fecha de descarga.
// - Copia de "Mis reservas" del servidor para consultarla sin conexión.
// - Se envían a POST /api/reservations/reservas/sync/ al recuperar la red,
//   al entrar a "Reservas" o con "Sincronizar ahora".
import 'dart:async';
import 'dart:convert';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:sqflite/sqflite.dart';
import 'package:uuid/uuid.dart';

import '../../../core/network/api_client.dart';
import '../../../core/offline/conexion.dart';
import '../../../core/offline/offline_db.dart';
import '../../../core/services/auth_service.dart';

class EstadoReservaLocal {
  static const String registrada = 'REGISTRADA';
  static const String enviada = 'ENVIADA';
  static const String confirmada = 'CONFIRMADA';
  static const String rechazada = 'RECHAZADA';
}

class ItemReservaLocal {
  final int idVariante;
  final String label;

  const ItemReservaLocal({required this.idVariante, required this.label});
}

class ReservaLocal {
  final String uuid;
  final int idSucursal;
  final String sucursal;
  final String fechaReserva;
  final String horaReserva;
  final DateTime fechaOperacion;
  final String estado;
  final String? mensaje;
  final int? idReserva;
  final DateTime? fechaConfirmacion;
  final List<ItemReservaLocal> items;

  const ReservaLocal({
    required this.uuid,
    required this.idSucursal,
    required this.sucursal,
    required this.fechaReserva,
    required this.horaReserva,
    required this.fechaOperacion,
    required this.estado,
    required this.mensaje,
    required this.idReserva,
    required this.fechaConfirmacion,
    required this.items,
  });

  factory ReservaLocal.fromFila(Map<String, Object?> f, List<ItemReservaLocal> items) {
    final confirmacion = f['fecha_confirmacion'] as String?;
    return ReservaLocal(
      uuid: f['uuid'] as String,
      idSucursal: f['id_sucursal'] as int,
      sucursal: (f['sucursal'] as String?) ?? '',
      fechaReserva: f['fecha_reserva'] as String,
      horaReserva: f['hora_reserva'] as String,
      fechaOperacion: DateTime.parse(f['fecha_operacion'] as String),
      estado: f['estado'] as String,
      mensaje: f['mensaje'] as String?,
      idReserva: f['id_reserva'] as int?,
      fechaConfirmacion: confirmacion != null ? DateTime.parse(confirmacion) : null,
      items: items,
    );
  }

  bool get porEnviar =>
      estado == EstadoReservaLocal.registrada || estado == EstadoReservaLocal.enviada;
}

class ResultadoSyncReservas {
  int sincronizadas = 0;
  int duplicadas = 0;
  int rechazadas = 0;
  String? error;
  final DateTime fecha;

  ResultadoSyncReservas(this.fecha);
}

class ReservaOfflineService extends ChangeNotifier {
  static const String _tipoSync = 'RESERVA';
  static const String _claveMisReservas = 'mis_reservas';
  static const String _recursoSucursales = 'sucursales_reserva';
  static const int _maxPorLote = 100;
  static const int _paginaCatalogo = 100;
  static const int _maxPaginasCatalogo = 20;
  static const Duration _intervaloReintento = Duration(seconds: 20);

  final ApiClient _api;
  final AuthService _auth;
  final OfflineDb _db = OfflineDb.instancia;
  final Uuid _uuid = const Uuid();

  bool _enLinea = true;
  bool _hayRed = true;
  bool _sincronizando = false;
  bool _comprobando = false;
  List<ReservaLocal> _reservas = [];
  ResultadoSyncReservas? _resultado;
  DateTime? _fechaCatalogo;
  int? _usuarioCargado;
  StreamSubscription<List<ConnectivityResult>>? _subConectividad;
  Timer? _timer;

  ReservaOfflineService({required ApiClient api, required AuthService auth})
      : _api = api,
        _auth = auth {
    _auth.addListener(_alCambiarSesion);
    _iniciar();
  }

  // ---------------------------------------------------------------- estado
  bool get enLinea => _enLinea;
  bool get sincronizando => _sincronizando;
  List<ReservaLocal> get reservas => List.unmodifiable(_reservas);
  ResultadoSyncReservas? get resultado => _resultado;
  DateTime? get fechaCatalogo => _fechaCatalogo;
  int get pendientes => _reservas.where((r) => r.porEnviar).length;
  int get confirmadas =>
      _reservas.where((r) => r.estado == EstadoReservaLocal.confirmada).length;
  int get rechazadas =>
      _reservas.where((r) => r.estado == EstadoReservaLocal.rechazada).length;

  int? get _idUsuario => _auth.currentUser?.idUsuario;

  /// Solo el cliente hace reservas (el endpoint de sincronización es del cliente).
  bool get _esCliente => _auth.currentUser?.hasRole('CLIENTE') ?? false;

  bool esErrorDeRedApi(Object error) => esErrorDeRed(error);

  // ---------------------------------------------------------------- conexión
  Future<void> _iniciar() async {
    try {
      _hayRed = tieneRed(await Connectivity().checkConnectivity());
      _enLinea = _hayRed;
    } catch (_) {
      // Si no se puede consultar, se asume en línea y lo corrige el primer error de red.
    }
    _subConectividad = Connectivity().onConnectivityChanged.listen((estado) {
      _hayRed = tieneRed(estado);
      if (_hayRed) {
        _comprobarServidor();
      } else {
        _cambiarEnLinea(false);
      }
    });
    _timer = Timer.periodic(_intervaloReintento, (_) => _comprobarServidor());
    await recargar();
    sincronizar();
  }

  void _cambiarEnLinea(bool valor) {
    if (_enLinea == valor) return;
    _enLinea = valor;
    notifyListeners();
  }

  void marcarSinConexion() => _cambiarEnLinea(false);

  Future<void> _comprobarServidor() async {
    if (_enLinea || !_hayRed || _comprobando || _idUsuario == null) return;
    _comprobando = true;
    try {
      await _api.dio.get(
        '/catalog/sucursales/',
        queryParameters: {'page_size': 1},
        options: Options(receiveTimeout: const Duration(seconds: 15)),
      );
      _volverEnLinea();
    } catch (e) {
      if (!esErrorDeRed(e)) _volverEnLinea();
    } finally {
      _comprobando = false;
    }
  }

  void _volverEnLinea() {
    _cambiarEnLinea(true);
    sincronizar();
  }

  void _alCambiarSesion() {
    if (_usuarioCargado == _idUsuario) return;
    _resultado = null;
    recargar().then((_) => sincronizar());
  }

  // ---------------------------------------------------------------- lectura local
  Future<void> recargar() async {
    final id = _idUsuario;
    _usuarioCargado = id;
    if (id == null) {
      _reservas = [];
      notifyListeners();
      return;
    }
    try {
      final db = await _db.db;
      final filas = await db.query(
        'reservas_local',
        where: 'id_usuario = ?',
        whereArgs: [id],
        orderBy: 'fecha_operacion DESC',
      );
      final filasItems = await db.rawQuery(
        'SELECT i.* FROM reserva_items_local i '
        'JOIN reservas_local r ON r.uuid = i.uuid_reserva '
        'WHERE r.id_usuario = ? ORDER BY i.id_item',
        [id],
      );
      final porReserva = <String, List<ItemReservaLocal>>{};
      for (final f in filasItems) {
        porReserva.putIfAbsent(f['uuid_reserva'] as String, () => []).add(
              ItemReservaLocal(idVariante: f['id_variante'] as int, label: f['label'] as String),
            );
      }
      _reservas = filas
          .map((f) => ReservaLocal.fromFila(f, porReserva[f['uuid']] ?? const []))
          .toList();

      final catalogo = await db.rawQuery('SELECT MAX(fecha_descarga) AS fecha FROM productos_local');
      final fecha = catalogo.isNotEmpty ? catalogo.first['fecha'] as String? : null;
      _fechaCatalogo = fecha != null ? DateTime.parse(fecha) : null;

      final ultimo = await db.query(
        'sync_resultados',
        where: 'id_usuario = ? AND tipo = ?',
        whereArgs: [id, _tipoSync],
        orderBy: 'fecha DESC',
        limit: 1,
      );
      if (ultimo.isNotEmpty) {
        final f = ultimo.first;
        _resultado = ResultadoSyncReservas(DateTime.parse(f['fecha'] as String))
          ..sincronizadas = f['sincronizadas'] as int
          ..duplicadas = f['duplicadas'] as int
          ..rechazadas = f['rechazadas'] as int
          ..error = f['error'] as String?;
      }
    } catch (_) {
      _reservas = [];
    }
    notifyListeners();
  }

  // ---------------------------------------------------------------- catálogo del cliente
  /// Descarga los productos (con variantes) y los guarda en SQLite.
  /// Devuelve la lista en el mismo formato JSON que /catalog/productos/.
  Future<List<Map<String, dynamic>>> descargarProductos() async {
    final productos = <Map<String, dynamic>>[];
    for (var pagina = 1; pagina <= _maxPaginasCatalogo; pagina++) {
      final response = await _api.dio.get(
        '/catalog/productos/',
        queryParameters: {'page_size': _paginaCatalogo, 'page': pagina},
      );
      final data = response.data;
      final filas = (data is Map ? (data['results'] ?? []) : data) as List;
      productos.addAll(filas.map((p) => Map<String, dynamic>.from(p as Map)));
      if (data is! Map || data['next'] == null) break;
    }
    await guardarProductos(productos);
    return productos;
  }

  /// Guarda (reemplaza) el catálogo local de productos y variantes.
  Future<void> guardarProductos(List<Map<String, dynamic>> productos) async {
    final ahora = DateTime.now().toUtc().toIso8601String();
    try {
      final db = await _db.db;
      await db.transaction((txn) async {
        // Al borrar productos se borran sus variantes (ON DELETE CASCADE).
        await txn.delete('productos_local');
        final batch = txn.batch();
        for (final p in productos) {
          batch.insert('productos_local', {
            'id_producto': p['id_producto'],
            'id_empresa': p['id_empresa'],
            'empresa_nombre': p['empresa_nombre'],
            'nombre': '${p['nombre'] ?? ''}',
            'descripcion': p['descripcion'],
            'genero': p['genero'],
            'tipo_prenda': p['tipo_prenda'],
            'categoria': (p['categoria'] is Map) ? p['categoria']['nombre'] : null,
            'marca': (p['marca'] is Map) ? p['marca']['nombre'] : null,
            'imagen_producto': p['imagen_producto'],
            'fecha_descarga': ahora,
          });
          for (final v in (p['variantes'] as List? ?? [])) {
            batch.insert(
              'variantes_producto_local',
              {
                'id_variante': v['id_variante'],
                'id_producto': p['id_producto'],
                'talla': (v['talla'] is Map) ? v['talla']['nombre'] : null,
                'color': (v['color'] is Map) ? v['color']['nombre'] : null,
                'codigo_hex': (v['color'] is Map) ? v['color']['codigo_hex'] : null,
                'codigo_producto': v['codigo_producto'],
                'precio': double.tryParse('${v['precio']}') ?? 0,
                'cantidad': int.tryParse('${v['cantidad']}') ?? 0,
                'imagen_variante': v['imagen_variante'],
                'estado': v['estado'],
              },
              conflictAlgorithm: ConflictAlgorithm.replace,
            );
          }
        }
        await batch.commit(noResult: true);
      });
      _fechaCatalogo = DateTime.parse(ahora);
      notifyListeners();
    } catch (_) {
      // Si no se pudo guardar, sin conexión se usa la copia anterior.
    }
  }

  /// Productos guardados, en el mismo formato JSON que /catalog/productos/
  /// (así las pantallas y Product.fromJson los usan igual).
  Future<List<Map<String, dynamic>>> productosLocales() async {
    final db = await _db.db;
    final productos = await db.query('productos_local', orderBy: 'nombre');
    final variantes = await db.query('variantes_producto_local', orderBy: 'id_variante');
    final porProducto = <int, List<Map<String, dynamic>>>{};
    for (final v in variantes) {
      porProducto.putIfAbsent(v['id_producto'] as int, () => []).add({
        'id_variante': v['id_variante'],
        'talla': v['talla'] != null ? {'nombre': v['talla']} : null,
        'color': v['color'] != null ? {'nombre': v['color'], 'codigo_hex': v['codigo_hex']} : null,
        'codigo_producto': v['codigo_producto'],
        'precio': v['precio'],
        'cantidad': v['cantidad'],
        'imagen_variante': v['imagen_variante'],
        'estado': v['estado'],
      });
    }
    return productos
        .map((p) => <String, dynamic>{
              'id_producto': p['id_producto'],
              'id_empresa': p['id_empresa'],
              'empresa_nombre': p['empresa_nombre'],
              'nombre': p['nombre'],
              'descripcion': p['descripcion'],
              'genero': p['genero'],
              'tipo_prenda': p['tipo_prenda'],
              'categoria': p['categoria'] != null ? {'nombre': p['categoria']} : null,
              'marca': p['marca'] != null ? {'nombre': p['marca']} : null,
              'imagen_producto': p['imagen_producto'],
              'variantes': porProducto[p['id_producto']] ?? [],
            })
        .toList();
  }

  // ---------------------------------------------------------------- sucursales
  /// Guarda solo las sucursales activas (con su tienda) para reservar sin conexión.
  Future<void> guardarSucursales(List<dynamic> sucursales) async {
    final id = _idUsuario;
    if (id == null) return;
    try {
      final db = await _db.db;
      final activas = sucursales.where((s) => s['estado'] == null || s['estado'] == 'ACTIVA');
      await db.transaction((txn) async {
        await txn.delete('sucursales_local', where: 'id_usuario = ?', whereArgs: [id]);
        final batch = txn.batch();
        for (final s in activas) {
          batch.insert(
            'sucursales_local',
            {
              'id_usuario': id,
              'id_sucursal': s['id_sucursal'] as int,
              'id_empresa': s['id_empresa'] is int ? s['id_empresa'] as int : null,
              'nombre': '${s['nombre'] ?? ''}',
            },
            conflictAlgorithm: ConflictAlgorithm.replace,
          );
        }
        batch.insert(
          'descargas_local',
          {
            'id_usuario': id,
            'recurso': _recursoSucursales,
            'fecha': DateTime.now().toUtc().toIso8601String(),
            'total': activas.length,
          },
          conflictAlgorithm: ConflictAlgorithm.replace,
        );
        await batch.commit(noResult: true);
      });
    } catch (_) {
      // Sin conexión se usa la copia anterior.
    }
  }

  Future<List<Map<String, dynamic>>> sucursalesLocales() async {
    final id = _idUsuario;
    if (id == null) return [];
    final db = await _db.db;
    final filas = await db.query(
      'sucursales_local',
      where: 'id_usuario = ?',
      whereArgs: [id],
      orderBy: 'nombre',
    );
    return filas
        .map((f) => <String, dynamic>{
              'id_sucursal': f['id_sucursal'],
              'id_empresa': f['id_empresa'],
              'nombre': f['nombre'],
              'estado': 'ACTIVA',
            })
        .toList();
  }

  // ---------------------------------------------------------------- copia de "Mis reservas"
  Future<void> guardarMisReservas(List<dynamic> reservas) async {
    final id = _idUsuario;
    if (id == null) return;
    try {
      final db = await _db.db;
      await db.insert(
        'cache_json',
        {
          'id_usuario': id,
          'clave': _claveMisReservas,
          'fecha': DateTime.now().toUtc().toIso8601String(),
          'datos': jsonEncode(reservas),
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    } catch (_) {
      // La copia es opcional.
    }
  }

  /// Copia guardada de "Mis reservas": (lista, fecha) o null si no hay.
  Future<(List<dynamic>, DateTime)?> misReservasLocales() async {
    final id = _idUsuario;
    if (id == null) return null;
    final db = await _db.db;
    final filas = await db.query(
      'cache_json',
      where: 'id_usuario = ? AND clave = ?',
      whereArgs: [id, _claveMisReservas],
    );
    if (filas.isEmpty) return null;
    return (
      jsonDecode(filas.first['datos'] as String) as List<dynamic>,
      DateTime.parse(filas.first['fecha'] as String),
    );
  }

  // ---------------------------------------------------------------- cola de reservas
  /// Guarda la reserva sin conexión y resta 1 de las existencias conocidas
  /// de cada prenda (una transacción).
  Future<ReservaLocal> guardar({
    required int idSucursal,
    required String sucursal,
    required int? idEmpresa,
    required String? empresaNombre,
    required String fechaReserva,
    required String horaReserva,
    required List<ItemReservaLocal> items,
  }) async {
    final id = _idUsuario;
    if (id == null) throw StateError('No hay una sesión iniciada.');
    final uuid = _uuid.v4();
    final ahora = DateTime.now().toUtc();
    final db = await _db.db;
    await db.transaction((txn) async {
      await txn.insert('reservas_local', {
        'uuid': uuid,
        'id_usuario': id,
        'id_empresa': idEmpresa,
        'empresa_nombre': empresaNombre,
        'id_sucursal': idSucursal,
        'sucursal': sucursal,
        'fecha_reserva': fechaReserva,
        'hora_reserva': horaReserva,
        'fecha_operacion': ahora.toIso8601String(),
        'estado': EstadoReservaLocal.registrada,
        'intentos': 0,
      });
      for (final item in items) {
        await txn.insert('reserva_items_local', {
          'uuid_reserva': uuid,
          'id_variante': item.idVariante,
          'label': item.label,
        });
      }
      await _ajustarExistencias(txn, items, -1);
    });
    await recargar();
    return _reservas.firstWhere((r) => r.uuid == uuid);
  }

  /// Solo se descartan las rechazadas; sus prendas vuelven a las existencias locales.
  Future<void> descartar(ReservaLocal reserva) async {
    final id = _idUsuario;
    if (id == null || reserva.estado != EstadoReservaLocal.rechazada) return;
    final db = await _db.db;
    await db.transaction((txn) async {
      await txn.delete('reservas_local',
          where: 'uuid = ? AND id_usuario = ?', whereArgs: [reserva.uuid, id]);
      await _ajustarExistencias(txn, reserva.items, 1);
    });
    await recargar();
  }

  Future<void> limpiarConfirmadas() async {
    final id = _idUsuario;
    if (id == null) return;
    final db = await _db.db;
    await db.delete('reservas_local',
        where: 'id_usuario = ? AND estado = ?',
        whereArgs: [id, EstadoReservaLocal.confirmada]);
    await recargar();
  }

  Future<void> _ajustarExistencias(Transaction txn, List<ItemReservaLocal> items, int signo) async {
    for (final item in items) {
      await txn.rawUpdate(
        'UPDATE variantes_producto_local SET cantidad = MAX(0, cantidad + ?) WHERE id_variante = ?',
        [signo, item.idVariante],
      );
    }
  }

  // ---------------------------------------------------------------- sincronización
  Future<ResultadoSyncReservas?> sincronizar() async {
    final id = _idUsuario;
    if (_sincronizando || id == null || !_esCliente || !_hayRed) return null;
    if (await _api.getToken() == null) return null;
    await recargar();
    final pendientes = _reservas.where((r) => r.porEnviar).toList()
      ..sort((a, b) => a.fechaOperacion.compareTo(b.fechaOperacion));
    if (pendientes.isEmpty) return null;

    _sincronizando = true;
    notifyListeners();
    final resultado = ResultadoSyncReservas(DateTime.now().toUtc());
    try {
      for (var i = 0; i < pendientes.length; i += _maxPorLote) {
        final fin = (i + _maxPorLote < pendientes.length) ? i + _maxPorLote : pendientes.length;
        await _enviarLote(pendientes.sublist(i, fin), resultado);
      }
    } catch (e) {
      resultado.error = _textoErrorSync(e);
      if (esErrorDeRed(e)) marcarSinConexion();
    } finally {
      _sincronizando = false;
      _resultado = resultado;
      await _guardarResultado(id, resultado);
      await recargar();
    }
    return resultado;
  }

  Future<void> _enviarLote(List<ReservaLocal> lote, ResultadoSyncReservas resultado) async {
    final db = await _db.db;
    final ahora = DateTime.now().toUtc().toIso8601String();
    final uuids = lote.map((r) => r.uuid).toList();
    final marcas = List.filled(uuids.length, '?').join(',');
    await db.rawUpdate(
      'UPDATE reservas_local SET estado = ?, intentos = intentos + 1, fecha_ultimo_intento = ? '
      'WHERE uuid IN ($marcas)',
      [EstadoReservaLocal.enviada, ahora, ...uuids],
    );
    await recargar();

    Response response;
    try {
      response = await _api.dio.post(
        '/reservations/reservas/sync/',
        data: {
          'operaciones': lote
              .map((r) => {
                    'uuid': r.uuid,
                    'fecha_operacion': r.fechaOperacion.toUtc().toIso8601String(),
                    'id_sucursal': r.idSucursal,
                    'fecha_reserva': r.fechaReserva,
                    'hora_reserva': r.horaReserva,
                    'items': r.items.map((i) => {'id_variante': i.idVariante}).toList(),
                  })
              .toList(),
        },
      );
    } catch (e) {
      // Sin respuesta válida: todo el lote vuelve a REGISTRADA para reintentar.
      await db.rawUpdate(
        'UPDATE reservas_local SET estado = ? WHERE uuid IN ($marcas)',
        [EstadoReservaLocal.registrada, ...uuids],
      );
      rethrow;
    }

    _cambiarEnLinea(true);
    final sinRespuesta = uuids.toSet();
    final resultados = (response.data is Map ? response.data['resultados'] : null) as List? ?? [];
    await db.transaction((txn) async {
      for (final r in resultados) {
        final uuid = r['uuid']?.toString();
        if (uuid == null || !sinRespuesta.remove(uuid)) continue;
        final estado = r['estado']?.toString();
        if (estado == 'SINCRONIZADA' || estado == 'DUPLICADA') {
          await txn.update(
            'reservas_local',
            {
              'estado': EstadoReservaLocal.confirmada,
              'id_reserva': r['id_reserva'] is int ? r['id_reserva'] as int : null,
              'fecha_confirmacion': DateTime.now().toUtc().toIso8601String(),
              'mensaje': estado == 'DUPLICADA' ? 'Ya estaba registrada en el servidor.' : null,
            },
            where: 'uuid = ?',
            whereArgs: [uuid],
          );
          if (estado == 'SINCRONIZADA') {
            resultado.sincronizadas += 1;
          } else {
            resultado.duplicadas += 1;
          }
        } else {
          await txn.update(
            'reservas_local',
            {
              'estado': EstadoReservaLocal.rechazada,
              'mensaje': r['mensaje']?.toString() ?? 'El servidor rechazó la reserva.',
            },
            where: 'uuid = ?',
            whereArgs: [uuid],
          );
          resultado.rechazadas += 1;
        }
      }
      for (final uuid in sinRespuesta) {
        await txn.update(
          'reservas_local',
          {'estado': EstadoReservaLocal.registrada},
          where: 'uuid = ?',
          whereArgs: [uuid],
        );
      }
    });
  }

  Future<void> _guardarResultado(int idUsuario, ResultadoSyncReservas r) async {
    try {
      final db = await _db.db;
      await db.insert('sync_resultados', {
        'id_usuario': idUsuario,
        'tipo': _tipoSync,
        'fecha': r.fecha.toIso8601String(),
        'sincronizadas': r.sincronizadas,
        'duplicadas': r.duplicadas,
        'rechazadas': r.rechazadas,
        'error': r.error,
      });
    } catch (_) {
      // El resultado igual se muestra en pantalla.
    }
  }

  String _textoErrorSync(Object error) {
    if (esErrorDeRed(error)) {
      return 'Sin conexión con el servidor. Las reservas siguen guardadas y se enviarán después.';
    }
    if (error is DioException) {
      if (error.response?.statusCode == 401) {
        return 'Tu sesión expiró. Inicia sesión de nuevo para enviar las reservas pendientes.';
      }
      final data = error.response?.data;
      if (data is Map) {
        if (data['detail'] != null) return data['detail'].toString();
        if (data['error'] != null) return data['error'].toString();
      }
    }
    return 'No se pudieron enviar las reservas pendientes.';
  }

  @override
  void dispose() {
    _auth.removeListener(_alCambiarSesion);
    _subConectividad?.cancel();
    _timer?.cancel();
    super.dispose();
  }
}
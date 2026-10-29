// mobile/lib/core/offline/cache_local.dart
//
// NUEVO: copias JSON de respuestas del servidor (tabla cache_json) para
// consultarlas sin conexión. Cada copia es del usuario de la sesión.
import 'dart:convert';

import 'package:sqflite/sqflite.dart';

import 'offline_db.dart';

class CacheLocal {
  CacheLocal._();

  /// Guarda (reemplaza) la copia [clave] del usuario.
  static Future<void> guardar(int idUsuario, String clave, Object datos) async {
    try {
      final db = await OfflineDb.instancia.db;
      await db.insert(
        'cache_json',
        {
          'id_usuario': idUsuario,
          'clave': clave,
          'fecha': DateTime.now().toUtc().toIso8601String(),
          'datos': jsonEncode(datos),
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    } catch (_) {
      // La copia es opcional: si falla, solo no habrá datos sin conexión.
    }
  }

  /// Copia guardada: (datos, fecha) o null si no hay.
  static Future<(dynamic, DateTime)?> leer(int idUsuario, String clave) async {
    try {
      final db = await OfflineDb.instancia.db;
      final filas = await db.query(
        'cache_json',
        where: 'id_usuario = ? AND clave = ?',
        whereArgs: [idUsuario, clave],
      );
      if (filas.isEmpty) return null;
      return (
        jsonDecode(filas.first['datos'] as String),
        DateTime.parse(filas.first['fecha'] as String),
      );
    } catch (_) {
      return null;
    }
  }
}
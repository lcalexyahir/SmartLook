// mobile/lib/features/admin/presentation/empresa_logo.dart
//
// NUEVO (SaaS): logo de la empresa como foto de perfil (base64 o URL);
// si no tiene o no se puede mostrar, sus iniciales.
import 'dart:convert';

import 'package:flutter/material.dart';
import '../../../shared/theme/app_colors.dart';

class EmpresaLogo extends StatelessWidget {
  final String? logo;
  final String nombre;
  final double tamano;

  const EmpresaLogo({super.key, required this.logo, required this.nombre, this.tamano = 56});

  String get _iniciales {
    final partes = nombre.trim().split(RegExp(r'\s+')).where((p) => p.isNotEmpty).toList();
    return partes.take(2).map((p) => p[0]).join().toUpperCase();
  }

  Widget _respaldo() {
    return Container(
      width: tamano,
      height: tamano,
      color: AppColors.primary,
      alignment: Alignment.center,
      child: Text(
        _iniciales,
        style: TextStyle(
          color: AppColors.white,
          fontWeight: FontWeight.bold,
          fontSize: tamano * 0.32,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    Widget imagen = _respaldo();
    final valor = logo ?? '';
    try {
      if (valor.startsWith('data:image') && valor.contains(',')) {
        imagen = Image.memory(
          base64Decode(valor.substring(valor.indexOf(',') + 1)),
          width: tamano,
          height: tamano,
          fit: BoxFit.cover,
          errorBuilder: (_, __, ___) => _respaldo(),
        );
      } else if (valor.startsWith('http')) {
        imagen = Image.network(
          valor,
          width: tamano,
          height: tamano,
          fit: BoxFit.cover,
          errorBuilder: (_, __, ___) => _respaldo(),
        );
      }
    } catch (_) {
      imagen = _respaldo();
    }
    return ClipOval(child: SizedBox(width: tamano, height: tamano, child: imagen));
  }
}
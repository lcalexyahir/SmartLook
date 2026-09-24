// mobile/lib/features/orders/presentation/devolucion_form_screen.dart
//
// NUEVO (devoluciones): pantalla para que el cliente elija qué prendas
// de un pedido con delivery ya entregado quiere devolver, con motivo
// por prenda. Se completa sola (sin aprobación de un encargado) y
// devuelve los mensajes de disculpa que manda el backend según el
// motivo, para mostrarlos en "Mis pedidos".

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/network/api_client.dart';
import '../../../shared/theme/app_colors.dart';

class _MotivoOpcion {
  final String value;
  final String label;
  const _MotivoOpcion(this.value, this.label);
}

const List<_MotivoOpcion> _motivos = [
  _MotivoOpcion('TALLA_INCORRECTA', 'Talla incorrecta'),
  _MotivoOpcion('COLOR_INCORRECTO', 'Color incorrecto'),
  _MotivoOpcion('PRODUCTO_DANADO', 'Producto dañado/defectuoso'),
  _MotivoOpcion('OTRO', 'Otro'),
];

class DevolucionFormScreen extends StatefulWidget {
  final Map<String, dynamic> pedido;

  const DevolucionFormScreen({super.key, required this.pedido});

  @override
  State<DevolucionFormScreen> createState() => _DevolucionFormScreenState();
}

class _DevolucionFormScreenState extends State<DevolucionFormScreen> {
  late final ApiClient _api;
  late List<Map<String, dynamic>> _items;
  bool _enviando = false;
  String _error = '';

  @override
  void initState() {
    super.initState();
    _api = context.read<ApiClient>();
    final itemsPedido = (widget.pedido['items'] ?? []) as List;
    _items = itemsPedido.map((i) {
      final m = Map<String, dynamic>.from(i as Map);
      return <String, dynamic>{
        'id_orden_item': m['id_item'],
        'variante': m['variante'],
        'cantidadMaxima': m['cantidad'],
        'cantidad': m['cantidad'],
        'motivo': 'TALLA_INCORRECTA',
        'incluir': false,
      };
    }).toList();
  }

  Future<void> _enviar() async {
    final seleccionados = _items.where((i) => i['incluir'] == true).toList();
    if (seleccionados.isEmpty) {
      setState(() => _error = 'Selecciona al menos una prenda a devolver.');
      return;
    }

    setState(() {
      _enviando = true;
      _error = '';
    });

    try {
      final response = await _api.dio.post(
        '/sales/devoluciones/solicitar/',
        data: {
          'id_orden': widget.pedido['id_orden'],
          'items': seleccionados
              .map((i) => {
                    'id_orden_item': i['id_orden_item'],
                    'cantidad': i['cantidad'],
                    'motivo': i['motivo'],
                  })
              .toList(),
        },
      );
      final mensajes = ((response.data['mensajes'] ?? []) as List)
          .map((m) => m.toString())
          .toList();
      if (!mounted) return;
      Navigator.pop(context, mensajes);
    } on DioException catch (e) {
      setState(() {
        _enviando = false;
        _error = _mensajeError(e);
      });
    } catch (_) {
      setState(() {
        _enviando = false;
        _error = 'No se pudo registrar la devolución. Intenta nuevamente.';
      });
    }
  }

  String _mensajeError(DioException e) {
    final data = e.response?.data;
    if (data is Map && data['error'] is String) {
      return data['error'] as String;
    }
    return 'No se pudo registrar la devolución. Intenta nuevamente.';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Devolver Pedido #${widget.pedido['id_orden']}')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (_error.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Text(_error, style: const TextStyle(color: AppColors.danger)),
            ),
          for (final item in _items) _tarjetaItem(item),
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _enviando ? null : _enviar,
              child: Text(_enviando ? 'Enviando...' : 'Confirmar devolución'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _tarjetaItem(Map<String, dynamic> item) {
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              controlAffinity: ListTileControlAffinity.leading,
              title: Text('${item['variante']} (compraste ${item['cantidadMaxima']})'),
              value: item['incluir'] as bool,
              onChanged: (v) => setState(() => item['incluir'] = v ?? false),
            ),
            if (item['incluir'] == true) ...[
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      initialValue: '${item['cantidad']}',
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(labelText: 'Cantidad'),
                      onChanged: (v) {
                        final n = int.tryParse(v);
                        if (n != null) item['cantidad'] = n;
                      },
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 2,
                    child: DropdownButtonFormField<String>(
                      value: item['motivo'] as String,
                      decoration: const InputDecoration(labelText: 'Motivo'),
                      items: _motivos
                          .map((m) => DropdownMenuItem(value: m.value, child: Text(m.label)))
                          .toList(),
                      onChanged: (v) => setState(() => item['motivo'] = v ?? item['motivo']),
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}
// mobile/lib/features/ai_assistant/presentation/chatbot_screen.dart
//
// CU18/CU19: panel del asistente virtual del cliente. Se abre como hoja
// inferior desde el globo de chat del catálogo (ChatBubbleFab).
import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/network/api_client.dart';
import '../../../shared/theme/app_colors.dart';
import '../../catalog/presentation/product_detail_screen.dart';
import '../services/ai_service.dart';

class _Mensaje {
  final bool esCliente;
  final String texto;
  final List<ChatCard> tarjetas;
  final bool esError;

  const _Mensaje({
    required this.esCliente,
    required this.texto,
    this.tarjetas = const [],
    this.esError = false,
  });
}

class ChatbotSheet extends StatefulWidget {
  final ApiClient apiClient;

  const ChatbotSheet({super.key, required this.apiClient});

  /// Abre el panel como hoja inferior sobre la pantalla actual.
  static Future<void> mostrar(BuildContext context) {
    final apiClient = context.read<ApiClient>();
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => ChatbotSheet(apiClient: apiClient),
    );
  }

  @override
  State<ChatbotSheet> createState() => _ChatbotSheetState();
}

class _ChatbotSheetState extends State<ChatbotSheet> {
  static const List<String> _sugerencias = [
    'Recomiéndame una polera',
    '¿Qué chaquetas tienen y cuánto cuestan?',
    '¿Qué sucursales tienen y en qué horario atienden?',
    '¿En qué estado está mi último pedido?',
  ];

  late final AiService _servicio;
  final TextEditingController _controlador = TextEditingController();
  final ScrollController _scroll = ScrollController();
  final List<_Mensaje> _mensajes = [];
  bool _cargandoHistorial = true;
  bool _enviando = false;

  @override
  void initState() {
    super.initState();
    _servicio = AiService(apiClient: widget.apiClient);
    _cargarHistorial();
  }

  @override
  void dispose() {
    _controlador.dispose();
    _scroll.dispose();
    super.dispose();
  }

  Future<void> _cargarHistorial() async {
    try {
      final items = await _servicio.historial();
      if (!mounted) return;
      setState(() {
        for (final item in items) {
          _mensajes.add(_Mensaje(esCliente: true, texto: item.mensaje));
          _mensajes.add(_Mensaje(esCliente: false, texto: item.respuesta));
        }
        _cargandoHistorial = false;
      });
      _irAlFinal();
    } catch (_) {
      if (!mounted) return;
      setState(() => _cargandoHistorial = false);
    }
  }

  Future<void> _enviar([String? texto]) async {
    final mensaje = (texto ?? _controlador.text).trim();
    if (mensaje.isEmpty || _enviando) return;
    setState(() {
      _mensajes.add(_Mensaje(esCliente: true, texto: mensaje));
      _controlador.clear();
      _enviando = true;
    });
    _irAlFinal();
    try {
      final respuesta = await _servicio.enviar(mensaje);
      if (!mounted) return;
      setState(() {
        _mensajes.add(
          _Mensaje(
            esCliente: false,
            texto: respuesta.respuesta,
            tarjetas: respuesta.tarjetas,
          ),
        );
        _enviando = false;
      });
    } on AiServiceException catch (e) {
      if (!mounted) return;
      setState(() {
        _mensajes.add(_Mensaje(esCliente: false, texto: e.message, esError: true));
        _enviando = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _mensajes.add(
          const _Mensaje(
            esCliente: false,
            texto: 'No pude responder en este momento. Intenta de nuevo en unos minutos.',
            esError: true,
          ),
        );
        _enviando = false;
      });
    }
    _irAlFinal();
  }

  void _irAlFinal() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(
          _scroll.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _verDetalle(ChatCard tarjeta) {
    final navegador = Navigator.of(context);
    navegador.pop();
    navegador.push(
      MaterialPageRoute(
        builder: (_) => ProductDetailScreen(productId: tarjeta.idProducto),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final medidas = MediaQuery.of(context);
    return Padding(
      padding: EdgeInsets.only(bottom: medidas.viewInsets.bottom),
      child: Container(
        height: medidas.size.height * 0.86,
        clipBehavior: Clip.antiAlias,
        decoration: const BoxDecoration(
          color: AppColors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        child: Column(
          children: [
            _encabezado(),
            Expanded(child: _lista()),
            if (_mensajes.isEmpty && !_cargandoHistorial && !_enviando)
              _sugerenciasRapidas(),
            _entrada(),
          ],
        ),
      ),
    );
  }

  Widget _encabezado() {
    return Container(
      color: AppColors.bgDeep,
      padding: const EdgeInsets.fromLTRB(16, 14, 8, 14),
      child: Row(
        children: [
          const CircleAvatar(
            radius: 19,
            backgroundColor: AppColors.primary,
            child: Text(
              'SL',
              style: TextStyle(
                color: AppColors.white,
                fontWeight: FontWeight.bold,
                fontSize: 13,
              ),
            ),
          ),
          const SizedBox(width: 12),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Asistente SmartLook',
                  style: TextStyle(
                    color: AppColors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  'Te ayudo a elegir tu próxima prenda',
                  style: TextStyle(color: AppColors.greyLight, fontSize: 12),
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.close, color: AppColors.white),
            tooltip: 'Cerrar',
            onPressed: () => Navigator.of(context).pop(),
          ),
        ],
      ),
    );
  }

  Widget _lista() {
    if (_cargandoHistorial) {
      return const Center(child: CircularProgressIndicator());
    }
    final items = <Widget>[];
    if (_mensajes.isEmpty) {
      items.add(
        _burbuja(
          const _Mensaje(
            esCliente: false,
            texto: '¡Hola! Soy el asistente de SmartLook. Puedo recomendarte '
                'prendas, decirte qué hay en cada sucursal y ayudarte con tus pedidos.',
          ),
        ),
      );
    }
    for (final m in _mensajes) {
      items.add(_burbuja(m));
      if (m.tarjetas.isNotEmpty) {
        items.add(Column(children: m.tarjetas.map(_tarjeta).toList()));
      }
    }
    if (_enviando) {
      items.add(_escribiendo());
    }
    return ListView(
      controller: _scroll,
      padding: const EdgeInsets.all(16),
      children: items,
    );
  }

  Widget _burbuja(_Mensaje m) {
    final Color fondo = m.esError
        ? AppColors.dangerBg
        : (m.esCliente ? AppColors.primary : AppColors.light);
    final Color colorTexto = m.esError
        ? AppColors.danger
        : (m.esCliente ? AppColors.white : AppColors.textDark);
    return Align(
      alignment: m.esCliente ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.78,
        ),
        decoration: BoxDecoration(
          color: fondo,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(m.esCliente ? 16 : 4),
            bottomRight: Radius.circular(m.esCliente ? 4 : 16),
          ),
        ),
        child: _conNegritas(
          m.texto,
          TextStyle(color: colorTexto, fontSize: 14.5, height: 1.35),
        ),
      ),
    );
  }

  // El modelo responde con un Markdown mínimo: viñetas ("* ", "- ") y **negrita**.
  Widget _conNegritas(String texto, TextStyle estilo) {
    final limpio = texto.replaceAll(
      RegExp(r'^[ \t]*[*-][ \t]+', multiLine: true),
      '• ',
    );
    final spans = <TextSpan>[];
    var ultimo = 0;
    for (final coincidencia in RegExp(r'\*\*(.+?)\*\*').allMatches(limpio)) {
      if (coincidencia.start > ultimo) {
        spans.add(TextSpan(text: limpio.substring(ultimo, coincidencia.start)));
      }
      spans.add(
        TextSpan(
          text: coincidencia.group(1),
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
      );
      ultimo = coincidencia.end;
    }
    if (ultimo < limpio.length) {
      spans.add(TextSpan(text: limpio.substring(ultimo)));
    }
    return Text.rich(TextSpan(style: estilo, children: spans));
  }

  Widget _tarjeta(ChatCard t) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.line),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: SizedBox(width: 72, height: 84, child: _imagen(t.imagen)),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  t.nombre,
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                ),
                const SizedBox(height: 2),
                Text(
                  t.precio,
                  style: const TextStyle(
                    color: AppColors.accent,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                if (t.tallas.isNotEmpty)
                  Text(
                    'Tallas: ${t.tallas.join(', ')}',
                    style: const TextStyle(fontSize: 12, color: AppColors.grey),
                  ),
                if (t.sucursales.isNotEmpty)
                  Text(
                    t.sucursales.first,
                    style: const TextStyle(fontSize: 12, color: AppColors.grey),
                  ),
                const SizedBox(height: 4),
                SizedBox(
                  height: 32,
                  child: ElevatedButton(
                    onPressed: () => _verDetalle(t),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: AppColors.white,
                      padding: const EdgeInsets.symmetric(horizontal: 14),
                    ),
                    child: const Text('Ver detalle', style: TextStyle(fontSize: 12)),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _imagen(String? url) {
    if (url == null) {
      return Container(
        color: AppColors.greyLight,
        child: const Icon(Icons.shopping_bag, color: AppColors.grey),
      );
    }
    return CachedNetworkImage(
      imageUrl: url,
      fit: BoxFit.cover,
      placeholder: (context, _) => Container(color: AppColors.greyLight),
      errorWidget: (context, _, __) => Container(
        color: AppColors.greyLight,
        child: const Icon(Icons.image_not_supported, color: AppColors.grey),
      ),
    );
  }

  Widget _escribiendo() {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: AppColors.light,
          borderRadius: BorderRadius.circular(16),
        ),
        child: const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            SizedBox(
              width: 16,
              height: 16,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
            SizedBox(width: 10),
            Text(
              'Escribiendo...',
              style: TextStyle(color: AppColors.grey, fontSize: 13),
            ),
          ],
        ),
      ),
    );
  }

  Widget _sugerenciasRapidas() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
      child: Wrap(
        spacing: 8,
        runSpacing: 4,
        children: _sugerencias
            .map(
              (s) => ActionChip(
                label: Text(s, style: const TextStyle(fontSize: 12.5)),
                side: const BorderSide(color: AppColors.primary),
                backgroundColor: AppColors.white,
                onPressed: () => _enviar(s),
              ),
            )
            .toList(),
      ),
    );
  }

  Widget _entrada() {
    return SafeArea(
      top: false,
      child: Container(
        padding: const EdgeInsets.fromLTRB(12, 8, 12, 8),
        decoration: const BoxDecoration(
          color: AppColors.white,
          border: Border(top: BorderSide(color: AppColors.line)),
        ),
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _controlador,
                maxLength: 500,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => _enviar(),
                decoration: InputDecoration(
                  hintText: 'Escribe tu consulta...',
                  counterText: '',
                  isDense: true,
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 10,
                  ),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                  ),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Container(
              decoration: BoxDecoration(
                color: _enviando ? AppColors.greyLight : AppColors.primary,
                shape: BoxShape.circle,
              ),
              child: IconButton(
                icon: const Icon(Icons.send, color: AppColors.white),
                tooltip: 'Enviar',
                onPressed: _enviando ? null : () => _enviar(),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
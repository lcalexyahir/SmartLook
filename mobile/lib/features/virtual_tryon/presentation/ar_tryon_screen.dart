// mobile/lib/features/virtual_tryon/presentation/ar_tryon_screen.dart
//
// CU17 - Vestidor Virtual (AR 2D).
//
// Pantalla del vestidor virtual: cámara en vivo a pantalla completa
// (proporción forzada a 3:4, recortando bordes sobrantes), con overlay
// PNG de la prenda reposicionado y escalado en cada frame según los
// hombros detectados por ML Kit Pose Detection.
//
// La traducción de landmark -> coordenada de pantalla (_traducirX/Y)
// sigue la misma lógica que la implementación de referencia oficial
// de ML Kit para Flutter: en Android, con cámara frontal, la imagen
// cruda del sensor viene "sin espejar" y en orientación horizontal
// (ancho/alto invertidos respecto a cómo se ve en pantalla vertical).
// Sin esto, el overlay queda desplazado y del lado equivocado.
//
// Es una aproximación simple (sin rig ni simulación de tela): asume
// que el cliente está de frente a la cámara.

import 'package:cached_network_image/cached_network_image.dart';
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:google_mlkit_commons/google_mlkit_commons.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:provider/provider.dart';

import '../../../core/network/api_client.dart';
import '../services/ar_service.dart';
import '../services/tryon_service.dart';


class ArTryOnScreen extends StatefulWidget {
  final int productoId;
  final String? overlayImageUrl;
  final String nombreProducto;

  const ArTryOnScreen({
    super.key,
    required this.productoId,
    required this.overlayImageUrl,
    required this.nombreProducto,
  });

  @override
  State<ArTryOnScreen> createState() => _ArTryOnScreenState();
}

class _ArTryOnScreenState extends State<ArTryOnScreen> {
  final ArService _arService = ArService();
  late final TryonService _tryonService;

  bool _cargando = true;
  String? _error;
  PoseFrame? _ultimoFrame;

  @override
  void initState() {
    super.initState();
    final apiClient = context.read<ApiClient>();
    _tryonService = TryonService(apiClient: apiClient);
    _inicializarTodo();
  }

  /// Pide el permiso de cámara, inicializa el servicio de AR y arranca
  /// la detección de poses en vivo. También registra la sesión en el
  /// backend (sin bloquear la UI si esa llamada falla).
  Future<void> _inicializarTodo() async {
    final estadoPermiso = await Permission.camera.request();
    if (!estadoPermiso.isGranted) {
      setState(() {
        _cargando = false;
        _error = 'Se necesita el permiso de cámara para usar el vestidor virtual.';
      });
      return;
    }

    try {
      await _arService.inicializar();
      await _arService.iniciarDeteccion((frame) {
        if (mounted) {
          setState(() {
            _ultimoFrame = frame;
          });
        }
      });

      _tryonService.registrarSesion(widget.productoId).catchError((_) {});

      setState(() {
        _cargando = false;
      });
    } catch (e) {
      setState(() {
        _cargando = false;
        _error = 'No se pudo inicializar la cámara: $e';
      });
    }
  }

  @override
  void dispose() {
    _arService.liberar();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        title: Text('Probando: ${widget.nombreProducto}'),
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
      ),
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Text(
                      _error!,
                      style: const TextStyle(color: Colors.white),
                      textAlign: TextAlign.center,
                    ),
                  ),
                )
              : _construirVestidor(),
    );
  }

  Widget _construirVestidor() {
    final controller = _arService.cameraController;
    if (controller == null || !controller.value.isInitialized) {
      return const Center(child: CircularProgressIndicator());
    }

    return LayoutBuilder(
      builder: (context, constraints) {
        final anchoPantalla = constraints.maxWidth;
        final altoPantalla = constraints.maxHeight;

        // Proporción de la caja de la cámara forzada a 3:4, agrandada
        // lo suficiente para CUBRIR toda la pantalla (recortando
        // bordes sobrantes con ClipRect más abajo, no dejando franjas
        // negras).
        const aspecto = 3 / 4;
        double boxAncho = anchoPantalla;
        double boxAlto = boxAncho / aspecto;
        if (boxAlto < altoPantalla) {
          boxAlto = altoPantalla;
          boxAncho = boxAlto * aspecto;
        }

        return ClipRect(
          child: Stack(
            fit: StackFit.expand,
            children: [
              OverflowBox(
                maxWidth: boxAncho,
                maxHeight: boxAlto,
                child: CameraPreview(controller),
              ),
              if (_ultimoFrame != null &&
                  _ultimoFrame!.esValido &&
                  widget.overlayImageUrl != null)
                _construirOverlay(
                  _ultimoFrame!,
                  anchoPantalla,
                  altoPantalla,
                  boxAncho,
                  boxAlto,
                ),
            ],
          ),
        );
      },
    );
  }

  /// Traduce la coordenada X de un landmark (en el espacio crudo de la
  /// imagen de la cámara) a coordenada X dentro de la caja de cámara
  /// en pantalla - compensando el espejado de la cámara frontal y el
  /// intercambio ancho/alto que ocurre en Android cuando la rotación
  /// es de 90° o 270°.
  double _traducirX(double x, double anchoCaja, Size imagenCruda, InputImageRotation rotation) {
    switch (rotation) {
      case InputImageRotation.rotation90deg:
        return x * anchoCaja / imagenCruda.height;
      case InputImageRotation.rotation270deg:
        return anchoCaja - (x * anchoCaja / imagenCruda.height);
      case InputImageRotation.rotation0deg:
      case InputImageRotation.rotation180deg:
        // Cámara frontal: siempre espejada en este caso.
        return anchoCaja - (x * anchoCaja / imagenCruda.width);
    }
  }

  /// Igual que [_traducirX] pero para la coordenada Y.
  double _traducirY(double y, double altoCaja, Size imagenCruda, InputImageRotation rotation) {
    switch (rotation) {
      case InputImageRotation.rotation90deg:
      case InputImageRotation.rotation270deg:
        return y * altoCaja / imagenCruda.width;
      case InputImageRotation.rotation0deg:
      case InputImageRotation.rotation180deg:
        return y * altoCaja / imagenCruda.height;
    }
  }

  /// Posiciona, escala y rota el PNG de la prenda según la distancia
  /// y el ángulo entre los hombros detectados en el frame actual.
  Widget _construirOverlay(
    PoseFrame frame,
    double anchoPantalla,
    double altoPantalla,
    double boxAncho,
    double boxAlto,
  ) {
    final hombroIzq = frame.hombroIzquierdo!;
    final hombroDer = frame.hombroDerecho!;

    final xIzqBox = _traducirX(hombroIzq.x, boxAncho, frame.imageSize, frame.rotation);
    final xDerBox = _traducirX(hombroDer.x, boxAncho, frame.imageSize, frame.rotation);
    final yIzqBox = _traducirY(hombroIzq.y, boxAlto, frame.imageSize, frame.rotation);
    final yDerBox = _traducirY(hombroDer.y, boxAlto, frame.imageSize, frame.rotation);

    final centroXBox = (xIzqBox + xDerBox) / 2;
    final yHombrosBox = (yIzqBox + yDerBox) / 2;
    final anchoHombrosBox = (xDerBox - xIzqBox).abs();

    // La prenda se dibuja ~2.0 veces más ancha que la distancia entre
    // hombros. AJUSTAR ACÁ si sigue viéndose muy ancha o angosta.
    final anchoOverlay = anchoHombrosBox * 2.0;
    final anguloRotacion =
        anchoHombrosBox == 0 ? 0.0 : (yDerBox - yIzqBox) / anchoHombrosBox;

    // La cámara se centró y agrandó para cubrir la pantalla - hay que
    // sumar ese mismo desplazamiento a la posición calculada.
    final offsetX = (anchoPantalla - boxAncho) / 2;
    final offsetY = (altoPantalla - boxAlto) / 2;

    final centroXPantalla = offsetX + centroXBox;
    final yHombrosPantalla = offsetY + yHombrosBox;

    return Positioned(
      left: centroXPantalla - (anchoOverlay / 2),
      // El cuello de la prenda sube más arriba de la línea de hombros
      // (14% del ancho de la prenda). AJUSTAR ACÁ si sigue apareciendo
      // muy abajo (subir el 0.14) o queda muy arriba (bajarlo).
      top: yHombrosPantalla - (anchoOverlay * 0.22),
      width: anchoOverlay,
      child: Transform.rotate(
        angle: anguloRotacion,
        child: CachedNetworkImage(
          imageUrl: widget.overlayImageUrl!,
          fit: BoxFit.contain,
          placeholder: (context, url) => const SizedBox.shrink(),
          errorWidget: (context, url, error) => const SizedBox.shrink(),
        ),
      ),
    );
  }
}
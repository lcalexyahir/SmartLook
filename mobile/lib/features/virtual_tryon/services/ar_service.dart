// mobile/lib/features/virtual_tryon/services/ar_service.dart
//
// CU17 - Vestidor Virtual (AR 2D).
//
// Envuelve la cámara del dispositivo y Google ML Kit Pose Detection.
// Expone, por cada frame de la cámara, los landmarks de pose (hombros
// y cadera) que la pantalla necesita para posicionar el overlay PNG
// de la prenda sobre el cuerpo del cliente.
//
// Solo Android (alcance del proyecto): usa el formato NV21, el único
// que ML Kit interpreta de forma confiable en este SO, y compensa la
// rotación combinando la orientación del sensor con la orientación
// real del dispositivo - el cálculo es distinto para cámara frontal
// que para trasera (se suma el ángulo, no se resta), según la propia
// documentación del plugin. La rotación calculada se expone en cada
// PoseFrame porque la pantalla la necesita para traducir correctamente
// las coordenadas del landmark a coordenadas de pantalla (ver
// ar_tryon_screen.dart).

import 'dart:ui';

import 'package:camera/camera.dart';
import 'package:flutter/services.dart';
import 'package:google_mlkit_pose_detection/google_mlkit_pose_detection.dart';


/// Resultado simplificado de un frame de pose: solo los puntos que el
/// overlay 2D necesita, en las coordenadas crudas de la imagen de la
/// cámara, más la rotación con la que se procesó ese frame.
class PoseFrame {
  final PoseLandmark? hombroIzquierdo;
  final PoseLandmark? hombroDerecho;
  final PoseLandmark? caderaIzquierda;
  final PoseLandmark? caderaDerecha;
  final Size imageSize;
  final InputImageRotation rotation;

  const PoseFrame({
    required this.hombroIzquierdo,
    required this.hombroDerecho,
    required this.caderaIzquierda,
    required this.caderaDerecha,
    required this.imageSize,
    required this.rotation,
  });

  /// Hay suficientes puntos para dibujar el overlay (al menos los dos
  /// hombros, que son los que definen ancho y rotación de la prenda).
  bool get esValido => hombroIzquierdo != null && hombroDerecho != null;
}


/// Administra el ciclo de vida de la cámara y el detector de poses.
///
/// Uso: inicializar() -> iniciarDeteccion(callback) -> ... -> liberar().
class ArService {
  CameraController? _cameraController;
  PoseDetector? _poseDetector;
  bool _procesandoFrame = false;
  late CameraDescription _camaraFrontal;
  InputImageRotation _ultimaRotacion = InputImageRotation.rotation0deg;

  CameraController? get cameraController => _cameraController;

  /// Ángulo (en grados) según la orientación física del dispositivo -
  /// tabla estándar usada por ML Kit para compensar la rotación.
  static const Map<DeviceOrientation, int> _orientaciones = {
    DeviceOrientation.portraitUp: 0,
    DeviceOrientation.landscapeLeft: 90,
    DeviceOrientation.portraitDown: 180,
    DeviceOrientation.landscapeRight: 270,
  };

  /// Inicializa la cámara frontal (selfie) y el detector de poses de
  /// ML Kit. Debe llamarse antes de iniciarDeteccion().
  Future<void> inicializar() async {
    final camaras = await availableCameras();
    _camaraFrontal = camaras.firstWhere(
      (c) => c.lensDirection == CameraLensDirection.front,
      orElse: () => camaras.first,
    );

    _cameraController = CameraController(
      _camaraFrontal,
      ResolutionPreset.medium,
      enableAudio: false,
      // NV21 es el único formato que ML Kit interpreta de forma
      // confiable en Android - sin esto, la cámara entrega YUV en
      // varios planos y la detección de pose nunca encuentra nada.
      imageFormatGroup: ImageFormatGroup.nv21,
    );
    await _cameraController!.initialize();

    // Fuerza que la cámara siempre entregue la imagen en orientación
    // vertical - evita que la vista previa aparezca rotada al usar
    // startImageStream() en paralelo, que es un problema conocido en
    // algunos dispositivos Android.
    await _cameraController!.lockCaptureOrientation(DeviceOrientation.portraitUp);

    _poseDetector = PoseDetector(
      options: PoseDetectorOptions(mode: PoseDetectionMode.stream),
    );
  }

  /// Empieza a procesar los frames de la cámara en vivo. Llama a
  /// [onFrame] cada vez que se detecta una pose en un frame nuevo.
  Future<void> iniciarDeteccion(void Function(PoseFrame) onFrame) async {
    if (_cameraController == null || _poseDetector == null) return;

    await _cameraController!.startImageStream((CameraImage imagen) async {
      // ML Kit procesa más lento que la tasa de frames de la cámara -
      // si no se descartan frames mientras el anterior sigue en
      // proceso, se van acumulando y la app se cuelga.
      if (_procesandoFrame) return;
      _procesandoFrame = true;

      try {
        final inputImage = _convertirImagen(imagen);
        if (inputImage == null) return;

        final poses = await _poseDetector!.processImage(inputImage);
        if (poses.isEmpty) return;

        final pose = poses.first;
        onFrame(
          PoseFrame(
            hombroIzquierdo: pose.landmarks[PoseLandmarkType.leftShoulder],
            hombroDerecho: pose.landmarks[PoseLandmarkType.rightShoulder],
            caderaIzquierda: pose.landmarks[PoseLandmarkType.leftHip],
            caderaDerecha: pose.landmarks[PoseLandmarkType.rightHip],
            imageSize: Size(
              imagen.width.toDouble(),
              imagen.height.toDouble(),
            ),
            rotation: _ultimaRotacion,
          ),
        );
      } finally {
        _procesandoFrame = false;
      }
    });
  }

  /// Convierte un CameraImage NV21 al InputImage que espera ML Kit,
  /// calculando la rotación correcta según el sensor de la cámara
  /// frontal y la orientación real del dispositivo en ese momento.
  InputImage? _convertirImagen(CameraImage imagen) {
    final orientacionDispositivo = _cameraController!.value.deviceOrientation;
    final gradosBase = _orientaciones[orientacionDispositivo];
    if (gradosBase == null) return null;

    // Para cámara frontal se SUMA el ángulo del sensor (para trasera
    // se resta) - así lo documenta el propio plugin de ML Kit.
    final rotacionCompensada =
        (_camaraFrontal.sensorOrientation + gradosBase) % 360;
    final rotation = InputImageRotationValue.fromRawValue(rotacionCompensada);
    if (rotation == null) return null;
    _ultimaRotacion = rotation;

    final format = InputImageFormatValue.fromRawValue(imagen.format.raw);
    // Solo NV21 es confiable en Android - si llegara otro formato,
    // se descarta el frame en vez de mandarle bytes mal interpretados
    // al detector.
    if (format == null || format != InputImageFormat.nv21) return null;
    if (imagen.planes.length != 1) return null;

    final plane = imagen.planes.first;

    return InputImage.fromBytes(
      bytes: plane.bytes,
      metadata: InputImageMetadata(
        size: Size(imagen.width.toDouble(), imagen.height.toDouble()),
        rotation: rotation,
        format: format,
        bytesPerRow: plane.bytesPerRow,
      ),
    );
  }

  /// Libera la cámara y el detector. Hay que llamarlo en el dispose()
  /// de la pantalla que use este servicio, o la cámara queda prendida.
  Future<void> liberar() async {
    await _cameraController?.stopImageStream();
    await _cameraController?.dispose();
    await _poseDetector?.close();
  }
}
import '../../../../core/models/product_model.dart';

class ProductEntity {
  final int id;
  final String nombre;
  final String? descripcion;
  final String tipoPrenda;
  final String? imagenProducto;
  final double precioMin;
  final double precioMax;
  final List<String> tallasDisponibles;
  final List<String> coloresDisponibles;
  final int stockTotal;

  ProductEntity({
    required this.id,
    required this.nombre,
    this.descripcion,
    required this.tipoPrenda,
    this.imagenProducto,
    required this.precioMin,
    required this.precioMax,
    required this.tallasDisponibles,
    required this.coloresDisponibles,
    required this.stockTotal,
  });

  factory ProductEntity.fromJson(Map<String, dynamic> json) {
    final product = Product.fromJson(json);
    final prices = product.variantes.map((v) => v.precio).toList();
    final tallas = product.variantes
        .map((v) => v.talla?.nombre ?? '')
        .where((t) => t.isNotEmpty)
        .toSet()
        .toList();
    final colores = product.variantes
        .map((v) => v.color?.nombre ?? '')
        .where((c) => c.isNotEmpty)
        .toSet()
        .toList();
    final stockTotal = product.variantes.fold<int>(0, (sum, v) => sum + v.cantidad);

    return ProductEntity(
      id: product.idProducto,
      nombre: product.nombre,
      descripcion: product.descripcion,
      tipoPrenda: product.tipoPrenda,
      imagenProducto: product.imagenProducto,
      precioMin: prices.isEmpty ? 0 : prices.reduce((a, b) => a < b ? a : b),
      precioMax: prices.isEmpty ? 0 : prices.reduce((a, b) => a > b ? a : b),
      tallasDisponibles: tallas,
      coloresDisponibles: colores,
      stockTotal: stockTotal,
    );
  }

  Product toModel() {
    return Product(
      idProducto: id,
      nombre: nombre,
      descripcion: descripcion,
      genero: 'MASCULINO',
      tipoPrenda: tipoPrenda,
      imagenProducto: imagenProducto,
      estado: 'ACTIVO',
      variantes: [],
    );
  }
}
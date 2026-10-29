// mobile/lib/features/catalog/domain/enties/product_entity.dart
//
// MODIFICADO (SaaS - A.1): conserva la tienda (empresa) del producto para
// que toModel() no la pierda (el catálogo usa toModel() para las tarjetas).
import '../../../../core/models/product_model.dart';

class ProductEntity {
  final int id;
  final int? idEmpresa;
  final String? empresaNombre;
  final String nombre;
  final String? descripcion;
  final String tipoPrenda;
  final String? imagenProducto;
  final double precioMin;
  final double precioMax;
  final List<String> tallasDisponibles;
  final List<String> coloresDisponibles;
  final int stockTotal;
  final List<ProductVariant> variantes;
  final Category? categoria;
  final Brand? marca;

  ProductEntity({
    required this.id,
    this.idEmpresa,
    this.empresaNombre,
    required this.nombre,
    this.descripcion,
    required this.tipoPrenda,
    this.imagenProducto,
    required this.precioMin,
    required this.precioMax,
    required this.tallasDisponibles,
    required this.coloresDisponibles,
    required this.stockTotal,
    required this.variantes,
    this.categoria,
    this.marca,
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
      idEmpresa: product.idEmpresa,
      empresaNombre: product.empresaNombre,
      nombre: product.nombre,
      descripcion: product.descripcion,
      tipoPrenda: product.tipoPrenda,
      imagenProducto: product.imagenProducto,
      precioMin: prices.isEmpty ? 0 : prices.reduce((a, b) => a < b ? a : b),
      precioMax: prices.isEmpty ? 0 : prices.reduce((a, b) => a > b ? a : b),
      tallasDisponibles: tallas,
      coloresDisponibles: colores,
      stockTotal: stockTotal,
      // Se guardan las variantes reales (ya vienen completas en el JSON
      // del listado) para que toModel() reconstruya un Product con precio real.
      variantes: product.variantes,
      categoria: product.categoria,
      marca: product.marca,
    );
  }

  Product toModel() {
    return Product(
      idProducto: id,
      idEmpresa: idEmpresa,
      empresaNombre: empresaNombre,
      categoria: categoria,
      marca: marca,
      nombre: nombre,
      descripcion: descripcion,
      genero: 'MASCULINO',
      tipoPrenda: tipoPrenda,
      imagenProducto: imagenProducto,
      estado: 'ACTIVO',
      variantes: variantes,
    );
  }
}
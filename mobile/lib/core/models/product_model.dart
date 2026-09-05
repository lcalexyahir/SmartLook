class Product {
  final int idProducto;
  final Category? categoria;
  final Brand? marca;
  final Season? temporada;
  final Collection? coleccion;
  final String nombre;
  final String? descripcion;
  final String genero;
  final String tipoPrenda;
  final String? imagenProducto;
  final String? modeloVirtual;
  final String estado;
  final List<ProductVariant> variantes;

  Product({
    required this.idProducto,
    this.categoria,
    this.marca,
    this.temporada,
    this.coleccion,
    required this.nombre,
    this.descripcion,
    required this.genero,
    required this.tipoPrenda,
    this.imagenProducto,
    this.modeloVirtual,
    required this.estado,
    required this.variantes,
  });

  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      idProducto: json['id_producto'] ?? 0,
      categoria: json['categoria'] != null
          ? Category.fromJson(json['categoria'])
          : null,
      marca: json['marca'] != null ? Brand.fromJson(json['marca']) : null,
      temporada: json['temporada'] != null
          ? Season.fromJson(json['temporada'])
          : null,
      coleccion: json['coleccion'] != null
          ? Collection.fromJson(json['coleccion'])
          : null,
      nombre: json['nombre'] ?? '',
      descripcion: json['descripcion'],
      genero: json['genero'] ?? 'MASCULINO',
      tipoPrenda: json['tipo_prenda'] ?? '',
      imagenProducto: json['imagen_producto'],
      modeloVirtual: json['modelo_virtual'],
      estado: json['estado'] ?? 'ACTIVO',
      variantes: (json['variantes'] as List<dynamic>? ?? [])
          .map((variant) => ProductVariant.fromJson(variant))
          .toList(),
    );
  }
}

class Category {
  final int idCategoria;
  final String nombre;
  final String? descripcion;
  final bool estado;

  Category({
    required this.idCategoria,
    required this.nombre,
    this.descripcion,
    required this.estado,
  });

  factory Category.fromJson(Map<String, dynamic> json) {
    return Category(
      idCategoria: json['id_categoria'] ?? 0,
      nombre: json['nombre'] ?? '',
      descripcion: json['descripcion'],
      estado: json['estado'] ?? true,
    );
  }
}

class Brand {
  final int idMarca;
  final String nombre;
  final String? descripcion;
  final bool estado;

  Brand({
    required this.idMarca,
    required this.nombre,
    this.descripcion,
    required this.estado,
  });

  factory Brand.fromJson(Map<String, dynamic> json) {
    return Brand(
      idMarca: json['id_marca'] ?? 0,
      nombre: json['nombre'] ?? '',
      descripcion: json['descripcion'],
      estado: json['estado'] ?? true,
    );
  }
}

class Season {
  final int idTemporada;
  final String nombre;
  final String? descripcion;
  final String? fechaInicio;
  final String? fechaFin;
  final bool estado;

  Season({
    required this.idTemporada,
    required this.nombre,
    this.descripcion,
    this.fechaInicio,
    this.fechaFin,
    required this.estado,
  });

  factory Season.fromJson(Map<String, dynamic> json) {
    return Season(
      idTemporada: json['id_temporada'] ?? 0,
      nombre: json['nombre'] ?? '',
      descripcion: json['descripcion'],
      fechaInicio: json['fecha_inicio'],
      fechaFin: json['fecha_fin'],
      estado: json['estado'] ?? true,
    );
  }
}

class Collection {
  final int idColeccion;
  final String nombre;
  final String? descripcion;
  final int? anio;
  final bool estado;

  Collection({
    required this.idColeccion,
    required this.nombre,
    this.descripcion,
    this.anio,
    required this.estado,
  });

  factory Collection.fromJson(Map<String, dynamic> json) {
    return Collection(
      idColeccion: json['id_coleccion'] ?? 0,
      nombre: json['nombre'] ?? '',
      descripcion: json['descripcion'],
      anio: json['anio'],
      estado: json['estado'] ?? true,
    );
  }
}

class ProductVariant {
  final int idVariante;
  final Size? talla;
  final Color? color;
  final String? codigoProducto;
  final double precio;
  final int cantidad;
  final String? imagenVariante;
  final String estado;

  ProductVariant({
    required this.idVariante,
    this.talla,
    this.color,
    this.codigoProducto,
    required this.precio,
    required this.cantidad,
    this.imagenVariante,
    required this.estado,
  });

  factory ProductVariant.fromJson(Map<String, dynamic> json) {
    return ProductVariant(
      idVariante: json['id_variante'] ?? 0,
      talla: json['talla'] != null ? Size.fromJson(json['talla']) : null,
      color: json['color'] != null ? Color.fromJson(json['color']) : null,
      codigoProducto: json['codigo_producto'],
      precio: (json['precio'] is String)
          ? double.tryParse(json['precio']) ?? 0.0
          : (json['precio'] ?? 0.0).toDouble(),
      cantidad: json['cantidad'] ?? 0,
      imagenVariante: json['imagen_variante'],
      estado: json['estado'] ?? 'DISPONIBLE',
    );
  }
}

class Size {
  final int idTalla;
  final String nombre;
  final String? descripcion;
  final bool estado;

  Size({
    required this.idTalla,
    required this.nombre,
    this.descripcion,
    required this.estado,
  });

  factory Size.fromJson(Map<String, dynamic> json) {
    return Size(
      idTalla: json['id_talla'] ?? 0,
      nombre: json['nombre'] ?? '',
      descripcion: json['descripcion'],
      estado: json['estado'] ?? true,
    );
  }
}

class Color {
  final int idColor;
  final String nombre;
  final String? codigoHex;
  final bool estado;

  Color({
    required this.idColor,
    required this.nombre,
    this.codigoHex,
    required this.estado,
  });

  factory Color.fromJson(Map<String, dynamic> json) {
    return Color(
      idColor: json['id_color'] ?? 0,
      nombre: json['nombre'] ?? '',
      codigoHex: json['codigo_hex'],
      estado: json['estado'] ?? true,
    );
  }

  int get colorValue {
    if (codigoHex != null && codigoHex!.startsWith('#')) {
      return int.tryParse(codigoHex!.substring(1), radix: 16) ?? 0xFF808080;
    }
    return 0xFF808080;
  }
}
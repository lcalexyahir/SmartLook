class Country {
  final int idPais;
  final String nombre;
  final bool estado;

  Country({
    required this.idPais,
    required this.nombre,
    required this.estado,
  });

  factory Country.fromJson(Map<String, dynamic> json) {
    return Country(
      idPais: json['id_pais'] ?? 0,
      nombre: json['nombre'] ?? '',
      estado: json['estado'] ?? true,
    );
  }
}

class City {
  final int idCiudad;
  final Country? pais;
  final String nombre;
  final bool estado;

  City({
    required this.idCiudad,
    this.pais,
    required this.nombre,
    required this.estado,
  });

  factory City.fromJson(Map<String, dynamic> json) {
    return City(
      idCiudad: json['id_ciudad'] ?? 0,
      pais: json['pais'] != null ? Country.fromJson(json['pais']) : null,
      nombre: json['nombre'] ?? '',
      estado: json['estado'] ?? true,
    );
  }
}

class Branch {
  final int idSucursal;
  final City? ciudad;
  final String nombre;
  final String direccion;
  final String? telefono;
  final String estado;
  final String? fechaApertura;

  Branch({
    required this.idSucursal,
    this.ciudad,
    required this.nombre,
    required this.direccion,
    this.telefono,
    required this.estado,
    this.fechaApertura,
  });

  factory Branch.fromJson(Map<String, dynamic> json) {
    return Branch(
      idSucursal: json['id_sucursal'] ?? 0,
      ciudad: json['ciudad'] != null ? City.fromJson(json['ciudad']) : null,
      nombre: json['nombre'] ?? '',
      direccion: json['direccion'] ?? '',
      telefono: json['telefono'],
      estado: json['estado'] ?? 'ACTIVA',
      fechaApertura: json['fecha_apertura'],
    );
  }
}

class Supplier {
  final int idProveedor;
  final String nombreEmpresa;
  final String? nombreContacto;
  final String? telefono;
  final String? correo;
  final String? direccion;
  final String estado;

  Supplier({
    required this.idProveedor,
    required this.nombreEmpresa,
    this.nombreContacto,
    this.telefono,
    this.correo,
    this.direccion,
    required this.estado,
  });

  factory Supplier.fromJson(Map<String, dynamic> json) {
    return Supplier(
      idProveedor: json['id_proveedor'] ?? 0,
      nombreEmpresa: json['nombre_empresa'] ?? '',
      nombreContacto: json['nombre_contacto'],
      telefono: json['telefono'],
      correo: json['correo'],
      direccion: json['direccion'],
      estado: json['estado'] ?? 'ACTIVO',
    );
  }
}
// mobile/lib/core/models/user_model.dart
//
// MODIFICADO (SaaS - A.2): el usuario trae su empresa y su sucursal
// (vacías para SUPER_ADMIN y clientes). Se agregan la pantalla de inicio
// según el rol (misma regla que la web) y copyWith().

class User {
  /// Roles que entran al panel (igual que ROLES_PERSONAL de la web).
  static const List<String> rolesPersonal = [
    'SUPER_ADMIN',
    'ADMIN_EMPRESA',
    'ENCARGADO_SUCURSAL',
    'CAJERO',
  ];

  final int idUsuario;
  final String nombres;
  final String apellidos;
  final String correo;
  final String? telefono;
  final String estado;
  final String? ultimoAcceso;
  final List<Role> roles;
  // NUEVO (SaaS): empresa (tenant) y sucursal del usuario.
  final int? idEmpresa;
  final String? empresaNombre;
  final int? idSucursal;
  final String? sucursalNombre;

  User({
    required this.idUsuario,
    required this.nombres,
    required this.apellidos,
    required this.correo,
    this.telefono,
    required this.estado,
    this.ultimoAcceso,
    required this.roles,
    this.idEmpresa,
    this.empresaNombre,
    this.idSucursal,
    this.sucursalNombre,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      idUsuario: json['id_usuario'] ?? 0,
      nombres: json['nombres'] ?? '',
      apellidos: json['apellidos'] ?? '',
      correo: json['correo'] ?? '',
      telefono: json['telefono'],
      estado: json['estado'] ?? 'ACTIVO',
      ultimoAcceso: json['ultimo_acceso'],
      roles: (json['roles'] as List<dynamic>? ?? [])
          .map((role) => Role.fromJson(role))
          .toList(),
      idEmpresa: json['id_empresa'] as int?,
      empresaNombre: json['empresa_nombre'] as String?,
      idSucursal: json['id_sucursal'] as int?,
      sucursalNombre: json['sucursal_nombre'] as String?,
    );
  }

  /// Copia con los datos personales cambiados (lo demás se conserva).
  User copyWith({String? nombres, String? apellidos, String? telefono}) {
    return User(
      idUsuario: idUsuario,
      nombres: nombres ?? this.nombres,
      apellidos: apellidos ?? this.apellidos,
      correo: correo,
      telefono: telefono ?? this.telefono,
      estado: estado,
      ultimoAcceso: ultimoAcceso,
      roles: roles,
      idEmpresa: idEmpresa,
      empresaNombre: empresaNombre,
      idSucursal: idSucursal,
      sucursalNombre: sucursalNombre,
    );
  }

  String get nombreCompleto => '$nombres $apellidos';

  bool hasRole(String roleName) {
    return roles.any((role) => role.nombre == roleName);
  }

  bool get esPersonal => roles.any((r) => rolesPersonal.contains(r.nombre));

  bool get esSoloRepartidor => hasRole('REPARTIDOR') && !esPersonal;

  /// Pantalla inicial según el rol.
  String get rutaInicio {
    if (esPersonal) return '/admin';
    if (esSoloRepartidor) return '/entregas';
    return '/catalog';
  }

  /// Nombre de la sucursal sin el nombre de la empresa delante
  /// ("FASHIONSTORE Ventura" -> "Ventura"), igual que en la web.
  String? get sucursalCorta {
    final nombre = sucursalNombre;
    if (nombre == null || nombre.isEmpty) return null;
    final empresa = empresaNombre ?? '';
    if (empresa.isNotEmpty && nombre.toUpperCase().startsWith('${empresa.toUpperCase()} ')) {
      final resto = nombre.substring(empresa.length + 1).trim();
      return resto.isEmpty ? nombre : resto;
    }
    return nombre;
  }
}

class Role {
  final int idRol;
  final String nombre;
  final String? descripcion;
  final bool estado;

  Role({
    required this.idRol,
    required this.nombre,
    this.descripcion,
    required this.estado,
  });

  factory Role.fromJson(Map<String, dynamic> json) {
    return Role(
      idRol: json['id_rol'] ?? 0,
      nombre: json['nombre'] ?? '',
      descripcion: json['descripcion'],
      estado: json['estado'] ?? true,
    );
  }
}
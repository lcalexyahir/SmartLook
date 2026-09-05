class User {
  final int idUsuario;
  final String nombres;
  final String apellidos;
  final String correo;
  final String? telefono;
  final String estado;
  final String? ultimoAcceso;
  final List<Role> roles;

  User({
    required this.idUsuario,
    required this.nombres,
    required this.apellidos,
    required this.correo,
    this.telefono,
    required this.estado,
    this.ultimoAcceso,
    required this.roles,
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
    );
  }

  String get nombreCompleto => '$nombres $apellidos';

  bool hasRole(String roleName) {
    return roles.any((role) => role.nombre == roleName);
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
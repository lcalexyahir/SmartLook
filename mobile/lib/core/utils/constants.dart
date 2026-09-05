class AppConstants {
  static const String appName = 'SmartLook';
  static const String appVersion = '1.0.0';
  
  static const String apiBaseUrl = 'http://10.0.2.2:8000/api';
  
  static const List<String> tallas = ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL'];
  
  static const List<String> generos = ['MASCULINO'];
  
  static const String defaultCurrency = 'Bs';
}

class ErrorMessages {
  static const String required = 'Este campo es requerido';
  static const String invalidEmail = 'Ingrese un correo válido';
  static const String passwordMismatch = 'Las contraseñas no coinciden';
  static const String minLength = 'Mínimo 6 caracteres';
}
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../../../core/services/auth_service.dart';
import '../../../core/utils/validators.dart';
import '../../../shared/theme/app_colors.dart';
import '../../../shared/widgets/custom_button.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nombresController = TextEditingController();
  final _apellidosController = TextEditingController();
  final _correoController = TextEditingController();
  final _telefonoController = TextEditingController();
  final _passwordController = TextEditingController();
  final _passwordConfirmController = TextEditingController();
  final _direccionController = TextEditingController();
  final _fechaNacimientoController = TextEditingController();
  bool _obscurePassword = true;
  bool _obscurePasswordConfirm = true;

  @override
  void dispose() {
    _nombresController.dispose();
    _apellidosController.dispose();
    _correoController.dispose();
    _telefonoController.dispose();
    _passwordController.dispose();
    _passwordConfirmController.dispose();
    _direccionController.dispose();
    _fechaNacimientoController.dispose();
    super.dispose();
  }

  Future<void> _handleRegister() async {
    if (!_formKey.currentState!.validate()) return;

    if (_passwordController.text != _passwordConfirmController.text) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Las contraseñas no coinciden'),
          backgroundColor: AppColors.danger,
        ),
      );
      return;
    }

    final authService = context.read<AuthService>();
    final success = await authService.register(
      nombres: _nombresController.text.trim(),
      apellidos: _apellidosController.text.trim(),
      correo: _correoController.text.trim(),
      telefono: _telefonoController.text.trim(),
      password: _passwordController.text,
      passwordConfirm: _passwordConfirmController.text,
      direccion: _direccionController.text.trim().isEmpty
          ? null
          : _direccionController.text.trim(),
      fechaNacimiento: _fechaNacimientoController.text.isEmpty
          ? null
          : _fechaNacimientoController.text,
    );

    if (!mounted) return;

    if (success) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Registro exitoso. Inicie sesión.'),
          backgroundColor: AppColors.success,
        ),
      );
      Navigator.pop(context);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(authService.errorMessage ?? 'Error al registrar'),
          backgroundColor: AppColors.danger,
        ),
      );
    }
  }

  InputDecoration _inputDecoration({required String label, required IconData icon, Widget? suffixIcon}) {
    return InputDecoration(
      labelText: label,
      labelStyle: GoogleFonts.inter(fontSize: 13, color: AppColors.textDark, fontWeight: FontWeight.w500),
      prefixIcon: Icon(icon, color: AppColors.grey, size: 20),
      suffixIcon: suffixIcon,
      filled: true,
      fillColor: AppColors.white,
      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(6),
        borderSide: BorderSide(color: AppColors.line),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(6),
        borderSide: BorderSide(color: AppColors.line),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(6),
        borderSide: const BorderSide(color: AppColors.primary, width: 1.5),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(6),
        borderSide: const BorderSide(color: AppColors.danger),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final authService = context.watch<AuthService>();

    return Scaffold(
      backgroundColor: AppColors.bgDeep,
      appBar: AppBar(
        backgroundColor: AppColors.bgDeep,
        elevation: 0,
        iconTheme: const IconThemeData(color: AppColors.panelBg),
        title: Text(
          'Registro',
          style: GoogleFonts.fraunces(
            fontSize: 18,
            fontWeight: FontWeight.w500,
            color: AppColors.panelBg,
          ),
        ),
      ),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              AppColors.bgDeep,
              AppColors.bgDeep2,
            ],
          ),
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: AppColors.panelBg,
                borderRadius: BorderRadius.circular(12),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.35),
                    blurRadius: 24,
                    offset: const Offset(0, 12),
                  ),
                ],
              ),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      'SmartLook',
                      style: GoogleFonts.fraunces(
                        fontSize: 22,
                        fontWeight: FontWeight.w500,
                        color: AppColors.textDark,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Crea tu cuenta como cliente',
                      style: GoogleFonts.inter(fontSize: 13, color: AppColors.grey),
                    ),
                    const SizedBox(height: 24),
                    Row(
                      children: [
                        Expanded(
                          child: TextFormField(
                            controller: _nombresController,
                            style: GoogleFonts.inter(fontSize: 14, color: AppColors.textDark),
                            decoration: _inputDecoration(label: 'Nombres', icon: Icons.person_outline),
                            validator: Validators.required,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: TextFormField(
                            controller: _apellidosController,
                            style: GoogleFonts.inter(fontSize: 14, color: AppColors.textDark),
                            decoration: _inputDecoration(label: 'Apellidos', icon: Icons.person_outline),
                            validator: Validators.required,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _correoController,
                      keyboardType: TextInputType.emailAddress,
                      style: GoogleFonts.inter(fontSize: 14, color: AppColors.textDark),
                      decoration: _inputDecoration(label: 'Correo Electrónico', icon: Icons.email_outlined),
                      validator: Validators.email,
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _telefonoController,
                      keyboardType: TextInputType.phone,
                      style: GoogleFonts.inter(fontSize: 14, color: AppColors.textDark),
                      decoration: _inputDecoration(label: 'Teléfono (Opcional)', icon: Icons.phone_outlined),
                      validator: Validators.phone,
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: TextFormField(
                            controller: _passwordController,
                            obscureText: _obscurePassword,
                            style: GoogleFonts.inter(fontSize: 14, color: AppColors.textDark),
                            decoration: _inputDecoration(
                              label: 'Contraseña',
                              icon: Icons.lock_outline,
                              suffixIcon: IconButton(
                                icon: Icon(
                                  _obscurePassword ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                                  color: AppColors.grey,
                                  size: 20,
                                ),
                                onPressed: () {
                                  setState(() {
                                    _obscurePassword = !_obscurePassword;
                                  });
                                },
                              ),
                            ),
                            validator: Validators.password,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: TextFormField(
                            controller: _passwordConfirmController,
                            obscureText: _obscurePasswordConfirm,
                            style: GoogleFonts.inter(fontSize: 14, color: AppColors.textDark),
                            decoration: _inputDecoration(
                              label: 'Confirmar',
                              icon: Icons.lock_outline,
                              suffixIcon: IconButton(
                                icon: Icon(
                                  _obscurePasswordConfirm ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                                  color: AppColors.grey,
                                  size: 20,
                                ),
                                onPressed: () {
                                  setState(() {
                                    _obscurePasswordConfirm = !_obscurePasswordConfirm;
                                  });
                                },
                              ),
                            ),
                            validator: Validators.password,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _direccionController,
                      style: GoogleFonts.inter(fontSize: 14, color: AppColors.textDark),
                      decoration: _inputDecoration(label: 'Dirección (Opcional)', icon: Icons.location_on_outlined),
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _fechaNacimientoController,
                      readOnly: true,
                      style: GoogleFonts.inter(fontSize: 14, color: AppColors.textDark),
                      decoration: _inputDecoration(label: 'Fecha de Nacimiento (Opcional)', icon: Icons.calendar_today_outlined),
                      onTap: () async {
                        final date = await showDatePicker(
                          context: context,
                          initialDate: DateTime(2000),
                          firstDate: DateTime(1950),
                          lastDate: DateTime.now(),
                        );
                        if (date != null) {
                          _fechaNacimientoController.text =
                              '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
                        }
                      },
                    ),
                    const SizedBox(height: 24),
                    CustomButton(
                      text: 'Registrarse',
                      isLoading: authService.isLoading,
                      onPressed: _handleRegister,
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
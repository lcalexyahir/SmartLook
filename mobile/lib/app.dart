// mobile/lib/app.dart
//
// MODIFICADO (SaaS - A.2): al restaurar la sesión, la pantalla inicial sale
// de User.rutaInicio (misma regla que el login).
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'shared/theme/app_theme.dart';
import 'core/services/auth_service.dart';
import 'features/auth/presentation/login_screen.dart';
import 'features/auth/presentation/register_screen.dart';
import 'features/client/presentation/client_home_screen.dart';
import 'features/admin/presentation/admin_home_screen.dart';
import 'features/pos/presentation/pos_cart_screen.dart';
import 'features/deliveries/presentation/deliveries_screen.dart';

class SmartLookApp extends StatelessWidget {
  const SmartLookApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SmartLook',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      initialRoute: '/',
      routes: {
        '/': (context) => const SplashScreen(),
        '/login': (context) => const LoginScreen(),
        '/register': (context) => const RegisterScreen(),
        '/catalog': (context) => const ClientHomeScreen(),
        '/admin': (context) => const AdminHomeScreen(),
        '/pos': (context) => const PosCartScreen(),
        '/entregas': (context) => const DeliveriesScreen(esInicio: true),
      },
    );
  }
}

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    await Future.delayed(const Duration(seconds: 2));
    if (!mounted) return;

    final authService = context.read<AuthService>();

    final sesionRestaurada = await authService.intentarRestaurarSesion();
    if (!mounted) return;

    if (!sesionRestaurada) {
      Navigator.pushReplacementNamed(context, '/login');
      return;
    }

    final ruta = authService.currentUser?.rutaInicio ?? '/catalog';
    Navigator.pushReplacementNamed(context, ruta);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1A1A2E),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.shopping_bag,
              size: 80,
              color: Colors.white,
            ),
            const SizedBox(height: 20),
            Text(
              'SmartLook',
              style: GoogleFonts.inter(
                fontSize: 32,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 10),
            Text(
              'Moda Masculina Premium',
              style: GoogleFonts.inter(
                fontSize: 14,
                color: Colors.white70,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
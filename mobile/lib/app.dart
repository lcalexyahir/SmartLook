import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'shared/theme/app_theme.dart';
import 'features/auth/presentation/login_screen.dart';
import 'features/catalog/presentation/product_list_screen.dart';
import 'package:provider/provider.dart';
import 'core/services/auth_service.dart';
import 'features/auth/presentation/register_screen.dart';
import 'features/auth/presentation/register_screen.dart';

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
        '/register': (context) => RegisterScreen(),
        '/catalog': (context) => const ProductListScreen(),
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
    if (authService.isAuthenticated) {
      Navigator.pushReplacementNamed(context, '/catalog');
    } else {
      Navigator.pushReplacementNamed(context, '/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1A1A2E),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.shopping_bag,
              size: 80,
              color: Colors.white,
            ),
            SizedBox(height: 20),
            Text(
              'SmartLook',
              style: GoogleFonts.inter(
                fontSize: 32,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            SizedBox(height: 10),
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
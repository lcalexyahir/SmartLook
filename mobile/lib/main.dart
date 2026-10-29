// mobile/lib/main.dart
//
// MODIFICADO (SaaS - 6.4): se registran los servicios sin conexión para toda
// la app (ventas POS y reservas), así la cola se envía al volver la red
// aunque el usuario no esté en esa pantalla.
import 'package:flutter/material.dart';
import 'package:flutter_stripe/flutter_stripe.dart';
import 'package:provider/provider.dart';
import 'app.dart';
import 'core/services/auth_service.dart';
import 'core/network/api_client.dart';
import 'features/pos/data/pos_offline_service.dart';
import 'features/reservations/data/reserva_offline_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Clave pública de Stripe (modo test). Es segura de exponer en el
  // cliente, a diferencia de la Secret key que solo vive en el backend.
  Stripe.publishableKey = 'pk_test_51UG4pEKnczxFoSWO6CqBqs3iN7mj3y9Q3ONCDNdbLYGKhDiBK6tJnd7tOm1sMRoDRG6DJSE7PSSyYz3dLGFtb9Dm00aJxcPj5k';
  await Stripe.instance.applySettings();

  final apiClient = ApiClient();
  final authService = AuthService(apiClient: apiClient);
  final posOffline = PosOfflineService(api: apiClient, auth: authService);
  final reservaOffline = ReservaOfflineService(api: apiClient, auth: authService);

  runApp(
    MultiProvider(
      providers: [
        Provider<ApiClient>.value(value: apiClient),
        ChangeNotifierProvider<AuthService>.value(value: authService),
        ChangeNotifierProvider<PosOfflineService>.value(value: posOffline),
        ChangeNotifierProvider<ReservaOfflineService>.value(value: reservaOffline),
      ],
      child: const SmartLookApp(),
    ),
  );
}
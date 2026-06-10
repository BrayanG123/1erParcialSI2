import 'package:flutter/material.dart';
import 'package:movil/config/routes.dart';
import 'package:movil/config/theme.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:movil/features/auth/bloc/auth_cubit.dart';
import 'package:movil/core/services/push_notification_service.dart'; 
import 'package:movil/features/cliente/services/sincronizacion_service.dart';


class AuxilioApp extends StatefulWidget {
  const AuxilioApp({super.key});

  @override
  State<AuxilioApp> createState() => _AuxilioAppState();
}

class _AuxilioAppState extends State<AuxilioApp> {
  // ── Servicio de sincronización ─────────────────────────────────────────────
  // Se inicia aquí y escucha la conectividad durante toda la vida de la app.
  final _sincronizacion = SincronizacionService();

  @override
  void initState() {
    super.initState();
    _sincronizacion.iniciar();

    // Inicializar FCM después del primer frame para tener BuildContext disponible
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        PushNotificationService().inicializar(context);
      }
    });
  }

  @override
  void dispose() {
    _sincronizacion.detener();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'AuxilioVehicular',
      theme: AppTheme.theme,
      routerConfig: appRouter,
      debugShowCheckedModeBanner: false,
    );
  }
}




// class AuxilioApp extends StatelessWidget {
//   const AuxilioApp({super.key});


//   @override
//   Widget build(BuildContext context) {

//     return BlocProvider(
//       create: (_) => AuthCubit()..verificarSesion(),
//       child: MaterialApp.router(
//         title: 'Auxilio Vehicular',
//         debugShowCheckedModeBanner: false,
//         theme: AppTheme.light,
//         routerConfig: appRouter,
//       ),
//     );
//   }
// }
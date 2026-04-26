import 'package:go_router/go_router.dart';
import 'package:movil/features/auth/screens/login_screen.dart';
import 'package:movil/features/auth/screens/register_cliente_screen.dart';
import 'package:movil/features/auth/screens/register_mecanico_screen.dart';
import 'package:movil/features/auth/screens/register_screen.dart';
import 'package:movil/features/auth/screens/splash_screen.dart';
import 'package:movil/features/home/screens/home_cliente_screen.dart';
import 'package:movil/features/home/screens/home_mecanico_screen.dart';
import 'package:movil/features/cliente/screens/solicitar_auxilio_screen.dart';
import 'package:movil/features/mecanico/screens/detalle_asignacion_screen.dart';



class AppRoutes {
  static const splash        = 'splash';
  static const login         = 'login';
  static const register      = 'register';
  static const registerCliente = 'register-cliente';
  static const registerMecanico    = 'register-mecanico';
  static const homeCliente   = 'home-cliente';
  static const homeMecanico  = 'home-mecanico';
  static const solicitarAuxilio = 'solicitar-auxilio';
  static const detalleAsignacion = 'detalle-asignacion';
}

final appRouter = GoRouter(

  initialLocation: '/',
  debugLogDiagnostics: true,

  routes: [

    GoRoute(
      path: '/', 
      name: AppRoutes.splash, 
      builder: (context, state) => const SplashScreen(),
    ),
    GoRoute(
      path: '/login',
      name: AppRoutes.login,
      builder: (context, state) => const LoginScreen(),
    ),
    GoRoute(
      path: '/registro',
      name: AppRoutes.register,
      builder: (context, state) => const RegisterScreen(),
    ),
    GoRoute(
      path: '/registro/cliente',
      name: AppRoutes.registerCliente,
      builder: (context, state) => const RegisterClienteScreen(),
    ),
    GoRoute(
      path: '/registro/mecanico',
      name: AppRoutes.registerMecanico,
      builder: (context, state) => const RegisterMecanicoScreen(),
    ),
    GoRoute(
      path: '/home/cliente',
      name: AppRoutes.homeCliente,
      builder: (context, state) => const HomeClienteScreen(),
    ),
    GoRoute(
      path: '/home/mecanico',
      name: AppRoutes.homeMecanico,
      builder: (context, state) => const HomeMecanicoScreen(),
    ),
    GoRoute(
      path: '/auxilio/nuevo',
      name: AppRoutes.solicitarAuxilio,
      builder: (context, state) => const SolicitarAuxilioScreen(),
    ),
    GoRoute(
      path: '/mecanico/asignacion/:id',
      name: AppRoutes.detalleAsignacion,
      builder: (context, state) {
        final id = state.extra as int;
        return DetalleAsignacionScreen(asignacionId: id);
      },
    ),
  ],

  
);

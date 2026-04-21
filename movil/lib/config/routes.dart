import 'package:go_router/go_router.dart';
import 'package:movil/features/auth/screens/login_screen.dart';
import 'package:movil/features/auth/screens/register_screen.dart';
import 'package:movil/features/auth/screens/splash_screen.dart';
import 'package:movil/features/home/screens/home_cliente_screen.dart';
import 'package:movil/features/home/screens/home_mecanico_screen.dart';




class AppRoutes {
  static const splash        = 'splash';
  static const login         = 'login';
  static const register      = 'register';
  static const homeCliente   = 'home-cliente';
  static const homeMecanico  = 'home-mecanico';
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
      path: '/home/cliente',
      name: AppRoutes.homeCliente,
      builder: (context, state) => const HomeClienteScreen(),
    ),
    GoRoute(
      path: '/home/mecanico',
      name: AppRoutes.homeMecanico,
      builder: (context, state) => const HomeMecanicoScreen(),
    ),
  ],

  
);

import 'package:go_router/go_router.dart';
import 'package:movil/features/auth/screens/login_screen.dart';
import 'package:movil/features/auth/screens/register_cliente_screen.dart';
import 'package:movil/features/auth/screens/register_mecanico_screen.dart';
import 'package:movil/features/auth/screens/register_screen.dart';
import 'package:movil/features/auth/screens/splash_screen.dart';
import 'package:movil/features/cliente/screens/form_vehiculo_screen.dart';
import 'package:movil/features/cliente/screens/home_cliente_screen.dart';
import 'package:movil/features/cliente/screens/solicitar_auxilio_screen.dart';
import 'package:movil/features/cliente/screens/vehiculos_screen.dart';
import 'package:movil/features/mecanico/screens/detalle_asignacion_screen.dart';
import 'package:movil/features/mecanico/screens/home_mecanico_screen.dart';
import 'package:movil/models/vehiculo.dart';
import 'package:movil/features/cliente/screens/detalle_incidente_screen.dart';
import 'package:movil/features/perfil/screens/perfil_screen.dart';


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
  static const vehiculos       = 'vehiculos';
  static const vehiculosPath   = '/cliente/vehiculos';  // constante de path base
  static const nuevoVehiculo   = 'nuevo-vehiculo';
  static const editarVehiculo  = 'editar-vehiculo';
  static const String detalleIncidente = 'detalle-incidente';
  static const perfil = 'perfil';


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

    GoRoute(
      path: '/cliente/vehiculos',
      name: AppRoutes.vehiculos,
      builder: (context, state) => const VehiculosScreen(),
      routes: [
        GoRoute(
          path: 'nuevo',
          name: AppRoutes.nuevoVehiculo,
          builder: (context, state) => const FormVehiculoScreen(),
        ),
        GoRoute(
          path: ':id/editar',
          name: AppRoutes.editarVehiculo,
          builder: (context, state) {
            final vehiculo = state.extra as Vehiculo;
            return FormVehiculoScreen(vehiculo: vehiculo);
          },
        ),
      ],
    ),

    GoRoute(
      path: '/cliente/incidente/:id',
      name: AppRoutes.detalleIncidente,
      builder: (context, state) {
        final id = int.parse(state.pathParameters['id']!);
        return DetalleIncidenteScreen(incidenteId: id);
      },
    ),

    GoRoute(
      path: '/perfil',
      name: AppRoutes.perfil,
      builder: (context, state) => const PerfilScreen(),
    ),
  ],

  
);

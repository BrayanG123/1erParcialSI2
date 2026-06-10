

class ApiConstants {

  // Auth
  static const String login            = '/auth/login';
  static const String registerCliente  = '/auth/registro/cliente';
  static const String registerMecanico = '/auth/registro/mecanico';

  // Usuarios
  static const String usuarios = '/usuarios';
  static const String usuarioMe = '/usuarios/me';

  // Vehículos
  static const String vehiculos = '/vehiculos';

  // Categorías
  static const String categorias = '/categorias';

  // Incidentes
  static const String incidentes = '/incidentes';

  // Asignaciones
  static const String asignaciones = '/asignaciones';

  // Servicios realizados
  static const String serviciosRealizados = '/servicios-realizados';

  // Pagos
  static const String pagos = '/pagos';

  // Comisiones
  static const String comisiones = '/comisiones';

  // Calificaciones
  static const String calificaciones = '/calificaciones';

  // Evidencias
  static const String evidencias = '/evidencias';

  // Historial de estados
  static const String historialEstados = '/historial-estados';

   // Notificaciones
  static const String pushToken = '/notificaciones/push-token';
  static const String misNotificaciones = '/notificaciones/mias';
  static const String notificacionesNoLeidas = '/notificaciones/no-leidas/conteo';
}
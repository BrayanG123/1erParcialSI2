import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:movil/core/network/api_exception.dart';
import 'package:movil/features/cliente/bloc/detalle_incidente_state.dart';
import 'package:movil/features/cliente/services/asignacion_cliente_service.dart';
import 'package:movil/features/cliente/services/calificacion_service.dart';
import 'package:movil/features/cliente/services/incidente_service.dart';
import 'package:movil/features/cliente/services/pago_service.dart';
import 'package:movil/features/cliente/services/servicio_realizado_cliente_service.dart';
import 'package:movil/models/asignacion_servicio.dart';



class DetalleIncidenteCubit extends Cubit<DetalleIncidenteState> {
  final IncidenteService          _incidenteService;
  final AsignacionClienteService  _asignacionService;
  final ServicioRealizadoClienteService  _servicioService;
  final PagoService                      _pagoService;
  final CalificacionService              _calificacionService;

  int? _incidenteIdActual; // para el botón "Reintentar"
  int? get incidenteIdActual => _incidenteIdActual;

  DetalleIncidenteCubit({
    IncidenteService?         incidenteService,
    AsignacionClienteService? asignacionService,
    ServicioRealizadoClienteService? servicioService,
    PagoService?                     pagoService,
    CalificacionService?             calificacionService,
  })  : _incidenteService  = incidenteService  ?? IncidenteService(),
        _asignacionService = asignacionService ?? AsignacionClienteService(),
        _servicioService     = servicioService     ?? ServicioRealizadoClienteService(),
        _pagoService         = pagoService         ?? PagoService(),
        _calificacionService = calificacionService ?? CalificacionService(),
        super(const DetalleIncidenteInitial());

  Future<void> cargar(int incidenteId) async {
    emit(const DetalleIncidenteCargando());

    try {
      final incidente = await _incidenteService.obtenerPorId(incidenteId);

      // ── Asignación (puede no existir) ─────────────────────────────────────
      AsignacionServicio? asignacion;
      try {
        asignacion = await _asignacionService.obtenerPorIncidente(incidenteId);
      } on ApiException catch (e) {
        if (e.statusCode != 404) rethrow;
      }

      // Solo cargamos servicio/pago/calificación si la asignación está completada
      if (asignacion == null ||
          asignacion.estado != EstadoAsignacion.completada) {
        emit(DetalleIncidenteCargado(
            incidente: incidente, asignacion: asignacion));
        return;
      }

      // ── Servicio realizado ─────────────────────────────────────────────────
      final servicio = await _servicioService
          .obtenerPorAsignacion(asignacion.id)
          .catchError((_) => null);

      if (servicio == null) {
        emit(DetalleIncidenteCargado(
            incidente: incidente, asignacion: asignacion));
        return;
      }

      // ── Pago (puede no existir aún) ────────────────────────────────────────
      dynamic pago;
      try {
        pago = await _pagoService.obtenerPorServicio(servicio.id);
      } on ApiException catch (e) {
        if (e.statusCode != 404) rethrow;
      }

      // ── Calificación (puede no existir aún) ───────────────────────────────
      dynamic calificacion;
      try {
        calificacion =
            await _calificacionService.obtenerPorServicio(servicio.id);
      } on ApiException catch (e) {
        if (e.statusCode != 404) rethrow;
      }

      emit(DetalleIncidenteCargado(
        incidente:    incidente,
        asignacion:   asignacion,
        servicio:     servicio,
        pago:         pago,
        calificacion: calificacion,
      ));

      // Intentamos obtener la asignación; si devuelve 404 simplemente no hay
      // try {
      //   final asignacion =
      //       await _asignacionService.obtenerPorIncidente(incidenteId);
      //   emit(DetalleIncidenteCargado(
      //       incidente: incidente, asignacion: asignacion));
      // } on ApiException catch (e) {
      //   if (e.statusCode == 404) {
      //     // Normal: aún no hay mecánico asignado
      //     emit(DetalleIncidenteCargado(incidente: incidente));
      //   } else {
      //     rethrow;
      //   }
      // }
    } on ApiException catch (e) {
      emit(DetalleIncidenteError(e.mensaje));
    } catch (_) {
      emit(const DetalleIncidenteError('Error al cargar el incidente.'));
    }
  }
}
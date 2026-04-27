import 'package:equatable/equatable.dart';
import 'package:movil/models/asignacion_servicio.dart';
import 'package:movil/models/incidente.dart';

import 'package:movil/models/calificacion.dart';
import 'package:movil/models/pago.dart';
import 'package:movil/models/servicio_realizado.dart';



abstract class DetalleIncidenteState extends Equatable {
  const DetalleIncidenteState();

  @override
  List<Object?> get props => [];
}


class DetalleIncidenteInitial extends DetalleIncidenteState {
  const DetalleIncidenteInitial();
}

class DetalleIncidenteCargando extends DetalleIncidenteState {
  const DetalleIncidenteCargando();
}

class DetalleIncidenteCargado extends DetalleIncidenteState {
  final Incidente incidente;
  final AsignacionServicio? asignacion; // null = aún sin asignar
  final ServicioRealizado?  servicio;   // null si aún no
  final Pago?               pago;       // null si no pagado
  final Calificacion?       calificacion; // null si no calificado

  const DetalleIncidenteCargado({
    required this.incidente,
    this.asignacion,
    this.servicio,
    this.pago,
    this.calificacion,
  });

  @override
  List<Object?> get props => [incidente, asignacion, servicio, pago, calificacion];
}


class DetalleIncidenteError extends DetalleIncidenteState {
  final String mensaje;

  const DetalleIncidenteError(this.mensaje);

  @override
  List<Object?> get props => [mensaje];
}
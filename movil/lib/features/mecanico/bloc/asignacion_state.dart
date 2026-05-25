import 'package:equatable/equatable.dart';
import 'package:movil/models/asignacion_servicio.dart';
import 'package:movil/models/servicio_realizado.dart';


abstract class AsignacionState extends Equatable {
  const AsignacionState();

  @override
  List<Object?> get props => [];
}

class AsignacionInitial extends AsignacionState {
  const AsignacionInitial();
}

class AsignacionCargando extends AsignacionState {
  const AsignacionCargando();
}

/// Lista de asignaciones cargada
class AsignacionListaCargada extends AsignacionState {
  final List<AsignacionServicio> asignaciones;

  const AsignacionListaCargada(this.asignaciones);

  @override
  List<Object?> get props => [asignaciones];
}

/// Una asignación individual cargada o actualizada
class AsignacionActualizada extends AsignacionState {
  final AsignacionServicio asignacion;

  const AsignacionActualizada(this.asignacion);

  @override
  List<Object?> get props => [asignacion];
}

/// Servicio registrado con éxito
class ServicioRegistrado extends AsignacionState {
  final ServicioRealizado servicio;

  const ServicioRegistrado(this.servicio);

  @override
  List<Object?> get props => [servicio];
}

class AsignacionError extends AsignacionState {
  final String mensaje;

  const AsignacionError(this.mensaje);

  @override
  List<Object?> get props => [mensaje];
}
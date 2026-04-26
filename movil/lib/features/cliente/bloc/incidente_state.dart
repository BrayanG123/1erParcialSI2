import 'package:equatable/equatable.dart';
import 'package:movil/models/categoria.dart';
import 'package:movil/models/incidente.dart';
import 'package:movil/models/vehiculo.dart';

abstract class IncidenteState extends Equatable {
  const IncidenteState();

  @override
  List<Object?> get props => [];
}

class IncidenteInitial extends IncidenteState {
  const IncidenteInitial();
}

class IncidenteCargando extends IncidenteState {
  const IncidenteCargando();
}

/// Datos cargados listos para mostrar el formulario
class IncidenteDatosCargados extends IncidenteState {
  final List<Vehiculo>  vehiculos;
  final List<Categoria> categorias;

  const IncidenteDatosCargados({
    required this.vehiculos,
    required this.categorias,
  });

  @override
  List<Object?> get props => [vehiculos, categorias];
}

/// El incidente fue creado con éxito
class IncidenteCreado extends IncidenteState {
  final Incidente incidente;

  const IncidenteCreado(this.incidente);

  @override
  List<Object?> get props => [incidente];
}

/// Lista de incidentes del cliente
class IncidenteListaCargada extends IncidenteState {
  final List<Incidente> incidentes;

  const IncidenteListaCargada(this.incidentes);

  @override
  List<Object?> get props => [incidentes];
}

class IncidenteError extends IncidenteState {
  final String mensaje;

  const IncidenteError(this.mensaje);

  @override
  List<Object?> get props => [mensaje];
}
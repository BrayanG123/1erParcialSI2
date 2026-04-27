import 'package:equatable/equatable.dart';
import 'package:movil/models/vehiculo.dart';


abstract class VehiculoState extends Equatable {
  const VehiculoState();
}

class VehiculoInitial extends VehiculoState {
  const VehiculoInitial();
  @override
  List<Object?> get props => [];
}


class VehiculoCargando extends VehiculoState {
  const VehiculoCargando();
  @override
  List<Object?> get props => [];
}

class VehiculoListaCargada extends VehiculoState {
  final List<Vehiculo> vehiculos;
  const VehiculoListaCargada(this.vehiculos);
  @override
  List<Object?> get props => [vehiculos];
}

/// Vehículo creado o actualizado exitosamente.
class VehiculoGuardado extends VehiculoState {
  final Vehiculo vehiculo;
  const VehiculoGuardado(this.vehiculo);
  @override
  List<Object?> get props => [vehiculo];
}

class VehiculoEliminado extends VehiculoState {
  const VehiculoEliminado();
  @override
  List<Object?> get props => [];
}

class VehiculoError extends VehiculoState {
  final String mensaje;
  const VehiculoError(this.mensaje);
  @override
  List<Object?> get props => [mensaje];
}
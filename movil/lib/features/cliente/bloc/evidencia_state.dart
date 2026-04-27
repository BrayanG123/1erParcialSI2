import 'package:equatable/equatable.dart';
import 'package:movil/models/evidencia.dart';


abstract class EvidenciaState extends Equatable {
  const EvidenciaState();
  @override
  List<Object?> get props => [];
}

class EvidenciaInitial  extends EvidenciaState { const EvidenciaInitial(); }
class EvidenciaCargando extends EvidenciaState { const EvidenciaCargando(); }

class EvidenciaError extends EvidenciaState {
  final String mensaje;
  const EvidenciaError(this.mensaje);
  @override List<Object?> get props => [mensaje];
}

class EvidenciasListas extends EvidenciaState {
  final List<Evidencia> lista;
  const EvidenciasListas(this.lista);
  @override List<Object?> get props => [lista];
}
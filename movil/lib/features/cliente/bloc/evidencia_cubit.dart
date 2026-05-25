import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:movil/core/network/api_exception.dart';
import 'package:movil/features/cliente/bloc/evidencia_state.dart';
import 'package:movil/features/cliente/services/evidencia_service.dart';
import 'package:movil/models/evidencia.dart';



class EvidenciaCubit extends Cubit<EvidenciaState> {
  final EvidenciaService _svc;

  EvidenciaCubit()
      : _svc = EvidenciaService(),
        super(const EvidenciaInitial());

  Future<void> cargar(int incidenteId) async {
    emit(const EvidenciaCargando());
    try {
      emit(EvidenciasListas(await _svc.listar(incidenteId)));
    } on ApiException catch (e) {
      emit(EvidenciaError(e.mensaje));
    }
  }

  Future<void> subirFoto(int incidenteId, String ruta) async {
    final prev = state is EvidenciasListas
        ? (state as EvidenciasListas).lista
        : <Evidencia>[];
    emit(const EvidenciaCargando());
    try {
      final nueva = await _svc.subirFoto(incidenteId, ruta);
      emit(EvidenciasListas([...prev, nueva]));
    } on ApiException catch (e) {
      emit(EvidenciasListas(prev));
      emit(EvidenciaError(e.mensaje));
    }
  }
}
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:movil/core/network/api_exception.dart';
import 'package:movil/features/mecanico/bloc/asignacion_state.dart';
import 'package:movil/features/mecanico/services/asignacion_service.dart';
import 'package:movil/features/mecanico/services/servicio_realizado_service.dart';
import 'package:movil/models/asignacion_servicio.dart';



class AsignacionCubit extends Cubit<AsignacionState>{

  final AsignacionService          _asignacionService;
  final ServicioRealizadoService   _servicioService;

  AsignacionCubit({
    AsignacionService?        asignacionService,
    ServicioRealizadoService? servicioService,
  })  : _asignacionService = asignacionService ?? AsignacionService(),
        _servicioService   = servicioService   ?? ServicioRealizadoService(),
        super(const AsignacionInitial());

  Future<void> cargarMisAsignaciones() async {
    emit(const AsignacionCargando());
    try {
      final lista = await _asignacionService.obtenerMisAsignaciones();
      emit(AsignacionListaCargada(lista));
    } on ApiException catch (e) {
      emit(AsignacionError(e.mensaje));
    } catch (_) {
      emit(const AsignacionError('Error al cargar las asignaciones.'));
    }
  }  

  Future<void> cargarAsignacion(int id) async {
    emit(const AsignacionCargando());
    try {
      final asignacion = await _asignacionService.obtenerPorId(id);
      emit(AsignacionActualizada(asignacion));
    } on ApiException catch (e) {
      emit(AsignacionError(e.mensaje));
    } catch (_) {
      emit(const AsignacionError('Error al cargar la asignación.'));
    }
  }

  Future<void> avanzarEstado(int id, EstadoAsignacion nuevoEstado) async {
    emit(const AsignacionCargando());
    try {
      final asignacion = await _asignacionService.avanzarEstado(id, nuevoEstado);
      emit(AsignacionActualizada(asignacion));
    } on ApiException catch (e) {
      emit(AsignacionError(e.mensaje));
    } catch (_) {
      emit(const AsignacionError('Error al actualizar el estado.'));
    }
  }


  Future<void> registrarServicio({
    required String tipoServicio,
    required String descripcionTrabajo,
    required double costoFinal,
    String? observaciones,
    required int asignacionId,
  }) async {
    emit(const AsignacionCargando());
    try {
      final servicio = await _servicioService.registrar(
        tipoServicio:       tipoServicio,
        descripcionTrabajo: descripcionTrabajo,
        costoFinal:         costoFinal,
        observaciones:      observaciones,
        asignacionId:       asignacionId,
      );
      emit(ServicioRegistrado(servicio));
    } on ApiException catch (e) {
      emit(AsignacionError(e.mensaje));
    } catch (_) {
      emit(const AsignacionError('Error al registrar el servicio.'));
    }
  }
  
}
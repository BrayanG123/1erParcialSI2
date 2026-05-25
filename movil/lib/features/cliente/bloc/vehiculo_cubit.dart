import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:movil/core/network/api_exception.dart';
import 'package:movil/features/cliente/bloc/vehiculo_state.dart';
import 'package:movil/features/cliente/services/vehiculo_service.dart';


class VehiculoCubit extends Cubit<VehiculoState> {

  final VehiculoService _service;

  VehiculoCubit({VehiculoService? service})
      : _service = service ?? VehiculoService(),
        super(const VehiculoInitial());

  // ── Cargar lista ────
  Future<void> cargarVehiculos() async {
    emit(const VehiculoCargando());
    try {
      final lista = await _service.obtenerMisVehiculos();
      emit(VehiculoListaCargada(lista));
    } on ApiException catch (e) {
      emit(VehiculoError(e.mensaje));
    } catch (_) {
      emit(const VehiculoError('Error al cargar los vehículos.'));
    }
  }

  // ── Crear ─────
  Future<void> crear({
    required String placa,
    required String modelo,
    required String color,
    String? tipoSeguro,
    String? rutaFoto,
  }) async {
    emit(const VehiculoCargando());
    try {
      var vehiculo = await _service.crear(
        placa: placa,
        modelo: modelo,
        color: color,
        tipoSeguro: tipoSeguro,
      );
      // Si se eligió una foto, subirla después de crear
      if (rutaFoto != null) {
        vehiculo = await _service.subirFoto(
          id: vehiculo.id,
          rutaFoto: rutaFoto,
        );
      }
      emit(VehiculoGuardado(vehiculo));
    } on ApiException catch (e) {
      emit(VehiculoError(e.mensaje));
    } catch (_) {
      emit(const VehiculoError('Error al guardar el vehículo.'));
    }
  }

  // ── Actualizar ─────
  Future<void> actualizar({
    required int id,
    String? modelo,
    String? color,
    String? tipoSeguro,
    String? rutaFoto,
  }) async {
    emit(const VehiculoCargando());
    try {
      var vehiculo = await _service.actualizar(
        id: id,
        modelo: modelo,
        color: color,
        tipoSeguro: tipoSeguro,
      );
      if (rutaFoto != null) {
        vehiculo = await _service.subirFoto(
          id: vehiculo.id,
          rutaFoto: rutaFoto,
        );
      }
      emit(VehiculoGuardado(vehiculo));
    } on ApiException catch (e) {
      emit(VehiculoError(e.mensaje));
    } catch (_) {
      emit(const VehiculoError('Error al actualizar el vehículo.'));
    }
  }


  // ── Eliminar ─────
  Future<void> eliminar(int id) async {
    emit(const VehiculoCargando());
    try {
      await _service.eliminar(id);
      emit(const VehiculoEliminado());
    } on ApiException catch (e) {
      emit(VehiculoError(e.mensaje));
    } catch (_) {
      emit(const VehiculoError('Error al eliminar el vehículo.'));
    }
  }
}
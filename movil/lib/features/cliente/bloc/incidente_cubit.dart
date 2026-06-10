import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:movil/core/network/api_exception.dart';
import 'package:movil/features/cliente/bloc/incidente_state.dart';
import 'package:movil/features/cliente/services/categoria_service.dart';
import 'package:movil/features/cliente/services/incidente_service.dart';
import 'package:movil/features/cliente/services/vehiculo_service.dart';

import 'dart:io';
import 'package:uuid/uuid.dart';
import 'package:movil/features/cliente/services/offline_incidente_service.dart';


class IncidenteCubit extends Cubit<IncidenteState>{
  final VehiculoService  _vehiculoService;
  final CategoriaService _categoriaService;
  final IncidenteService _incidenteService;
  final OfflineIncidenteService _offlineService;

  IncidenteCubit({
    VehiculoService?  vehiculoService,
    CategoriaService? categoriaService,
    IncidenteService? incidenteService,
    OfflineIncidenteService? offlineService,
  })  : _vehiculoService  = vehiculoService  ?? VehiculoService(),
        _categoriaService = categoriaService ?? CategoriaService(),
        _incidenteService = incidenteService ?? IncidenteService(),
        _offlineService   = offlineService   ?? OfflineIncidenteService(),
        super(const IncidenteInitial());


  /// Carga vehículos y categorías para poblar el formulario.
  Future<void> cargarDatosFormulario() async {
    emit(const IncidenteCargando());
    try {
      final resultados = await Future.wait([
        _vehiculoService.obtenerMisVehiculos(),
        _categoriaService.obtenerCategorias(),
      ]);
      emit(IncidenteDatosCargados(
        vehiculos:  resultados[0] as dynamic,
        categorias: resultados[1] as dynamic,
      ));
    } on ApiException catch (e) {
      emit(IncidenteError(e.mensaje));
    } catch (_) {
      emit(const IncidenteError('Error al cargar los datos.'));
    }
  }

  /// Crea un nuevo incidente.
  Future<void> crearIncidente({
    required String descripcion,
    required double latitud,
    required double longitud,
    required int clienteId,
    int? vehiculoId,
    int? categoriaId,
    String? rutaFoto,   
    String? rutaAudio,
  }) async {
    emit(const IncidenteCargando());
    try {
      var incidente = await _incidenteService.crearIncidente(
        descripcion: descripcion,
        latitud:     latitud,
        longitud:    longitud,
        clienteId:   clienteId,
        vehiculoId:  vehiculoId,
        categoriaId: categoriaId,
      );

      // Subir foto si existe
      if (rutaFoto != null) {
        incidente = await _incidenteService.subirFoto(
          incidenteId: incidente.id,
          rutaFoto:    rutaFoto,
        );
      }

      // Subir audio si existe 
      if (rutaAudio != null) {
        incidente = await _incidenteService.subirAudio(
          incidenteId: incidente.id,
          rutaAudio:   rutaAudio,
        );
      }

      emit(IncidenteCreado(incidente));
    } on ApiException catch (e) {
      emit(IncidenteError(e.mensaje));
    } catch (_) {
      // No se pudo conectar con el servidor.
      // Guardar el incidente localmente para sincronizar después.

      // Generar un ID único local para identificar este intento
      const uuid = Uuid();
      final pendiente = IncidentePendiente(
        idempotencyKey: uuid.v4(),
        descripcion:    descripcion,
        latitud:        latitud,
        longitud:       longitud,
        clienteId:      clienteId,
        vehiculoId:     vehiculoId,
        categoriaId:    categoriaId,
        rutaFoto:       rutaFoto,
        rutaAudio:      rutaAudio,
        timestamp:      DateTime.now(),
      );

      await _offlineService.guardar(pendiente);

      emit(IncidenteGuardadoOffline(
        totalPendientes: _offlineService.cantidadPendientes,
      ));
    }
  }

  /// Carga el historial de incidentes del cliente.
  Future<void> cargarMisIncidentes() async {
    emit(const IncidenteCargando());
    try {
      final lista = await _incidenteService.obtenerMisIncidentes();
      emit(IncidenteListaCargada(lista));
    } on ApiException catch (e) {
      emit(IncidenteError(e.mensaje));
    } catch (_) {
      emit(const IncidenteError('Error al cargar tus solicitudes.'));
    }
  }
}
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:movil/config/theme.dart';
import 'package:movil/features/mecanico/bloc/asignacion_cubit.dart';
import 'package:movil/features/mecanico/bloc/asignacion_state.dart';
import 'package:movil/models/asignacion_servicio.dart';


class DetalleAsignacionScreen extends StatelessWidget {
  final int asignacionId;

  const DetalleAsignacionScreen({super.key, required this.asignacionId});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => AsignacionCubit()..cargarAsignacion(asignacionId),
      child: const _DetalleView(),
    );
  }
}


class _DetalleView extends StatelessWidget {
  const _DetalleView();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.fondo,
      appBar: AppBar(title: const Text('Detalle de asignación')),
      body: BlocConsumer<AsignacionCubit, AsignacionState>(
        listener: (context, state) {
          if (state is AsignacionError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.mensaje),
                backgroundColor: AppTheme.peligro,
              ),
            );
          }
          if (state is ServicioRegistrado) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('Servicio registrado con éxito.'),
                backgroundColor: AppTheme.exito,
              ),
            );
            Navigator.of(context).pop(); // cierra el diálogo si sigue abierto
          }
        },
        builder: (context, state) {
          if (state is AsignacionCargando) {
            return const Center(child: CircularProgressIndicator());
          }

          AsignacionServicio? asignacion;
          if (state is AsignacionActualizada) {
            asignacion = state.asignacion;
          }

          if (asignacion == null) {
            return const Center(
              child: Text('No se pudo cargar la asignación.'),
            );
          }

          return SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _FichaInfo(asignacion: asignacion),
                const SizedBox(height: 24),
                _BotonesAccion(asignacion: asignacion),
              ],
            ),
          );
        },
      ),
    );
  }
}


// --- Ficha de información ---
class _FichaInfo extends StatelessWidget {
  final AsignacionServicio asignacion;
  const _FichaInfo({required this.asignacion});

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _Fila('Asignación', '#${asignacion.id}'),
            _Fila('Incidente',  '#${asignacion.incidenteId}'),
            _Fila('Estado',     _etiquetaEstado(asignacion.estado)),
            if (asignacion.distanciaKm != null)
              _Fila('Distancia', '${asignacion.distanciaKm!.toStringAsFixed(1)} km'),
            if (asignacion.tiempoEstimado != null)
              _Fila('Tiempo estimado', '${asignacion.tiempoEstimado} min'),
            if (asignacion.costoEstimado != null)
              _Fila('Costo estimado', 'Bs. ${asignacion.costoEstimado!.toStringAsFixed(2)}'),
            if (asignacion.motivoRechazo != null)
              _Fila('Motivo rechazo', asignacion.motivoRechazo!),
          ],
        ),
      ),
    );
  }

  String _etiquetaEstado(EstadoAsignacion e) {
    const map = {
      EstadoAsignacion.pendiente:   'Pendiente',
      EstadoAsignacion.aceptada:    'Aceptada',
      EstadoAsignacion.enCamino:    'En camino',
      EstadoAsignacion.enServicio:  'En servicio',
      EstadoAsignacion.completada:  'Completada',
      EstadoAsignacion.rechazada:   'Rechazada',
      EstadoAsignacion.cancelada:   'Cancelada',
    };
    return map[e] ?? e.name;
  }
}


class _Fila extends StatelessWidget {
  final String label;
  final String valor;
  const _Fila(this.label, this.valor);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          SizedBox(
            width: 140,
            child: Text(
              label,
              style: const TextStyle(
                  color: AppTheme.textoSecundario, fontSize: 13),
            ),
          ),
          Expanded(
            child: Text(
              valor,
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }
}


// --- Botones de acción según estado ---
class _BotonesAccion extends StatelessWidget {
  final AsignacionServicio asignacion;
  const _BotonesAccion({required this.asignacion});

  @override
  Widget build(BuildContext context) {
    final cubit = context.read<AsignacionCubit>();

    return switch (asignacion.estado) {
      EstadoAsignacion.aceptada => FilledButton.icon(
          onPressed: () =>
              cubit.avanzarEstado(asignacion.id, EstadoAsignacion.enCamino),
          icon: const Icon(Icons.directions_car),
          label: const Text('Ir al lugar'),
          style: FilledButton.styleFrom(
            minimumSize: const Size.fromHeight(48),
            shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12)),
          ),
        ),

      EstadoAsignacion.enCamino => FilledButton.icon(
          onPressed: () =>
              cubit.avanzarEstado(asignacion.id, EstadoAsignacion.enServicio),
          icon: const Icon(Icons.build),
          label: const Text('Iniciar servicio'),
          style: FilledButton.styleFrom(
            backgroundColor: AppTheme.acento,
            minimumSize: const Size.fromHeight(48),
            shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12)),
          ),
        ),

      EstadoAsignacion.enServicio => FilledButton.icon(
          onPressed: () =>
              _mostrarDialogoServicio(context, cubit, asignacion.id),
          icon: const Icon(Icons.task_alt),
          label: const Text('Completar servicio'),
          style: FilledButton.styleFrom(
            backgroundColor: AppTheme.exito,
            minimumSize: const Size.fromHeight(48),
            shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12)),
          ),
        ),

        _ => const SizedBox.shrink(), // completada / cancelada
    };
  }

  void _mostrarDialogoServicio(BuildContext context, AsignacionCubit cubit, int asignacionId) {

    final tipoCtrl   = TextEditingController();
    final descCtrl   = TextEditingController();
    final costoCtrl  = TextEditingController();
    final obsCtrl    = TextEditingController();
    final formKey    = GlobalKey<FormState>();

    showDialog(
      context: context, 
      builder: (_) => AlertDialog(
        title: const Text('Registrar servicio'),
        content: SingleChildScrollView(
          child: Form(
            key: formKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextFormField(
                  controller: tipoCtrl,
                  decoration: const InputDecoration(
                      labelText: 'Tipo de servicio',
                      border: OutlineInputBorder()),
                  validator: (v) => v == null || v.isEmpty ? 'Requerido' : null,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: descCtrl,
                  decoration: const InputDecoration(
                      labelText: 'Descripción del trabajo',
                      border: OutlineInputBorder()),
                  maxLines: 2,
                  validator: (v) => v == null || v.isEmpty ? 'Requerido' : null,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: costoCtrl,
                  decoration: const InputDecoration(
                      labelText: 'Costo final (Bs.)',
                      border: OutlineInputBorder()),
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  validator: (v) {
                    if (v == null || v.isEmpty) return 'Requerido';
                    if (double.tryParse(v) == null) return 'Número inválido';
                    return null;
                  },
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: obsCtrl,
                  decoration: const InputDecoration(
                      labelText: 'Observaciones (opcional)',
                      border: OutlineInputBorder()),
                  maxLines: 2,
                ),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () {
              if (!formKey.currentState!.validate()) return;
              Navigator.pop(context);
              cubit.registrarServicio(
                tipoServicio:       tipoCtrl.text.trim(),
                descripcionTrabajo: descCtrl.text.trim(),
                costoFinal:         double.parse(costoCtrl.text.trim()),
                observaciones:      obsCtrl.text.trim(),
                asignacionId:       asignacionId,
              );
            },
            style: FilledButton.styleFrom(backgroundColor: AppTheme.exito),
            child: const Text('Guardar'),
          ),
        ],
      ),
    );
  }
}
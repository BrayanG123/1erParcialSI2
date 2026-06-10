import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:movil/config/theme.dart';
import 'package:movil/features/cliente/bloc/detalle_incidente_cubit.dart';
import 'package:movil/features/cliente/bloc/detalle_incidente_state.dart';
import 'package:movil/features/cliente/screens/pago_screen.dart';
import 'package:movil/features/cliente/services/calificacion_service.dart';
import 'package:movil/models/asignacion_servicio.dart';
import 'package:movil/models/incidente.dart';
import 'package:movil/models/servicio_realizado.dart';
import 'package:movil/models/pago.dart';
import 'package:movil/models/calificacion.dart';
import 'package:movil/features/cliente/bloc/evidencia_cubit.dart';
import 'package:movil/features/cliente/bloc/evidencia_state.dart';
import 'package:movil/models/evidencia.dart';

import 'package:go_router/go_router.dart';
import 'package:movil/config/routes.dart';


class DetalleIncidenteScreen extends StatelessWidget {
  final int incidenteId;

  const DetalleIncidenteScreen({super.key, required this.incidenteId});

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider( create: (_) => DetalleIncidenteCubit()..cargar(incidenteId), ),
        BlocProvider(create: (_) => EvidenciaCubit()..cargar(incidenteId)),
      ],
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
      appBar: AppBar(title: const Text('Mi solicitud')),
      body: BlocBuilder<DetalleIncidenteCubit,
      DetalleIncidenteState>(
        builder: (context, state) {
          if (state is DetalleIncidenteCargando) {
            return const Center(child: CircularProgressIndicator());
          }

          if (state is DetalleIncidenteError) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline,
                      size: 48, color: AppTheme.peligro),
                  const SizedBox(height: 12),
                  Text(state.mensaje,
                      textAlign: TextAlign.center,
                      style:
                          const TextStyle(color: AppTheme.textoSecundario)),
                  const SizedBox(height: 16),
                  TextButton(
                    onPressed: () =>
                        context.read<DetalleIncidenteCubit>().cargar(
                              (context
                                      .read<DetalleIncidenteCubit>()
                                      .state as dynamic)
                                  .incidenteId ??
                                  0,
                            ),
                    child: const Text('Reintentar'),
                  ),
                ],
              ),
            );
          }

          if (state is DetalleIncidenteCargado) {
            return RefreshIndicator(
              onRefresh: () => context
                  .read<DetalleIncidenteCubit>()
                  .cargar(state.incidente.id),
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    _CardIncidente(incidente: state.incidente),
                    const SizedBox(height: 20),



                    if (state.incidente.fotoIncidente != null) ...[
                      _CardFoto(url: state.incidente.fotoIncidente!),
                      const SizedBox(height: 20),
                    ],
                    _CardEvidencias(incidenteId: state.incidente.id),
                    const SizedBox(height: 20),
                    _CardAsignacion(asignacion: state.asignacion, incidenteId: state.incidente.id),



                    if (state.servicio != null) ...[
                      const SizedBox(height: 20),
                      _CardServicioCompletado(
                        servicio: state.servicio!,
                        pago: state.pago,
                        onPagar: () => Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => PagoScreen(
                              servicio: state.servicio!,
                              onPagoRegistrado: () =>
                                  context.read<DetalleIncidenteCubit>().cargar(state.incidente.id),
                            ),
                          ),
                        ),
                      ),
                    ],
                    if (state.pago != null && state.calificacion == null) ...[
                      const SizedBox(height: 12),
                      _BotonCalificar(
                        servicioId: state.servicio!.id,
                        onCalificado: () =>
                            context.read<DetalleIncidenteCubit>().cargar(state.incidente.id),
                      ),
                    ],
                    if (state.calificacion != null) ...[
                      const SizedBox(height: 12),
                      _CardCalificacion(calificacion: state.calificacion!),
                    ],
                  ],
                ),
              ),
            );
          }
        
          return const SizedBox.shrink();
        },
      ),
    );
  }
}


// ─── Card: información del incidente ────────────────────────────────────────
class _CardIncidente extends StatelessWidget {

  final Incidente incidente;
  const _CardIncidente({required this.incidente});

  @override
  Widget build(BuildContext context) {
    final color = incidente.estado == EstadoIncidente.disponible
        ? AppTheme.advertencia
        : AppTheme.exito;
    final etiqueta = incidente.estado == EstadoIncidente.disponible
        ? 'Pendiente'
        : 'Atendido';

    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.report_problem_outlined,
                    color: AppTheme.primario),
                const SizedBox(width: 8),
                const Text('Solicitud',
                    style: TextStyle(
                        fontWeight: FontWeight.bold, fontSize: 16)),
                const Spacer(),
                Chip(
                  label: Text(etiqueta,
                      style: TextStyle(color: color, fontSize: 12)),
                  backgroundColor: color.withValues(alpha: 0.12),
                  side: BorderSide.none,
                ),
              ],
            ),
            const Divider(height: 24),
            Text(incidente.descripcion,
                style: const TextStyle(fontSize: 15)),
            const SizedBox(height: 12),
            _Fila(
              icon: Icons.calendar_today_outlined,
              texto:
                  '${incidente.fechaHora.day}/${incidente.fechaHora.month}/${incidente.fechaHora.year}  '
                  '${incidente.fechaHora.hour.toString().padLeft(2, '0')}:'
                  '${incidente.fechaHora.minute.toString().padLeft(2, '0')}',
            ),
            _Fila(
              icon: Icons.location_on_outlined,
              texto:
                  '${incidente.latitud.toStringAsFixed(5)}, ${incidente.longitud.toStringAsFixed(5)}',
            ),
            if (incidente.resumenIa != null) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppTheme.primario.withValues(alpha: 0.06),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.auto_awesome,
                        color: AppTheme.primario, size: 18),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        incidente.resumenIa!,
                        style: const TextStyle(
                            fontSize: 13, color: AppTheme.textoSecundario),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

// ─── Card: foto del incidente ────────────────────────────────────────────────
class _CardFoto extends StatelessWidget {
  final String url;
  const _CardFoto({required this.url});

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.fromLTRB(16, 16, 16, 8),
            child: Row(
              children: [
                Icon(Icons.photo_outlined, color: AppTheme.primario),
                SizedBox(width: 8),
                Text('Foto adjunta',
                    style: TextStyle(
                        fontWeight: FontWeight.bold, fontSize: 15)),
              ],
            ),
          ),
          Image.network(
            url,
            width: double.infinity,
            height: 200,
            fit: BoxFit.cover,
            errorBuilder: (_, __, ___) => const SizedBox(
              height: 80,
              child: Center(
                  child: Text('No se pudo cargar la foto',
                      style: TextStyle(color: AppTheme.textoSecundario))),
            ),
          ),
        ],
      ),
    );
  }
}


// ─── Card: estado de la asignación ──────────────────────────────────────────
class _CardAsignacion extends StatelessWidget {
  final AsignacionServicio? asignacion;
  final int incidenteId;
  const _CardAsignacion({this.asignacion, required this.incidenteId});

  @override
  Widget build(BuildContext context) {
    if (asignacion == null) {
      return Card(
        shape:
            RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        child: const Padding(
          padding: EdgeInsets.all(20),
          child: Row(
            children: [
              Icon(Icons.hourglass_empty,
                  color: AppTheme.advertencia),
              SizedBox(width: 12),
              Expanded(
                child: Text(
                  'Esperando que un taller acepte tu solicitud…',
                  style: TextStyle(color: AppTheme.textoSecundario),
                ),
              ),
            ],
          ),
        ),
      );
    }

    return Card(
      shape:
          RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.build_circle_outlined,
                    color: AppTheme.primario),
                const SizedBox(width: 8),
                const Text('Mecánico asignado',
                    style: TextStyle(
                        fontWeight: FontWeight.bold, fontSize: 16)),
                const Spacer(),
                _ChipEstado(estado: asignacion!.estado),
              ],
            ),
            const Divider(height: 24),
            _Fila(
              icon: Icons.tag,
              texto: 'Asignación #${asignacion!.id}',
            ),
            if (asignacion!.costoEstimado != null)
              _Fila(
                icon: Icons.attach_money,
                texto:
                    'Costo estimado: Bs ${asignacion!.costoEstimado!.toStringAsFixed(2)}',
              ),
            if (asignacion!.tiempoEstimado != null)
              _Fila(
                icon: Icons.access_time,
                texto:
                    'Tiempo estimado: ${asignacion!.tiempoEstimado} min',
              ),
            if (asignacion!.motivoRechazo != null) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppTheme.peligro.withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.cancel_outlined,
                        color: AppTheme.peligro, size: 18),
                    const SizedBox(width: 8),
                    Expanded(
                        child: Text(asignacion!.motivoRechazo!,
                            style: const TextStyle(
                                color: AppTheme.peligro))),
                  ],
                ),
              ),
            ],

            // ── NUEVO: botón de tracking ───────────────────────────────────────────
            if (asignacion?.estado == EstadoAsignacion.enCamino ||
                asignacion?.estado == EstadoAsignacion.enServicio) ...[
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () {
                    context.pushNamed(
                      AppRoutes.trackingIncidente,
                      pathParameters: {'id': incidenteId.toString()},
                    );
                  },
                  icon: const Icon(Icons.location_on),
                  label: const Text('Ver mecánico en tiempo real'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
              ),
            ],

            // Barra de progreso (estados)
            const SizedBox(height: 16),
            _BarraProgreso(estado: asignacion!.estado),
          ],
        ),
      ),
    );
  }
}

// ─── Chip de estado con color dinámico ──────────────────────────────────────
class _ChipEstado extends StatelessWidget {
  final EstadoAsignacion estado;
  const _ChipEstado({required this.estado});

  (Color, String) get _info {
    return switch (estado) {
      EstadoAsignacion.pendiente  => (AppTheme.advertencia, 'Pendiente'),
      EstadoAsignacion.aceptada   => (AppTheme.primario,    'Aceptada'),
      EstadoAsignacion.rechazada  => (AppTheme.peligro,     'Rechazada'),
      EstadoAsignacion.enCamino   => (AppTheme.primario,    'En camino'),
      EstadoAsignacion.enServicio => (AppTheme.exito,       'En servicio'),
      EstadoAsignacion.completada => (AppTheme.exito,       'Completada'),
      EstadoAsignacion.cancelada  => (AppTheme.peligro,     'Cancelada'),
    };
  }

  @override
  Widget build(BuildContext context) {
    final (color, texto) = _info;
    return Chip(
      label:
          Text(texto, style: TextStyle(color: color, fontSize: 12)),
      backgroundColor: color.withValues(alpha: 0.12),
      side: BorderSide.none,
    );
  }
}

// ─── Barra de progreso visual ────────────────────────────────────────────────
class _BarraProgreso extends StatelessWidget {
  final EstadoAsignacion estado;
  const _BarraProgreso({required this.estado});

  static const _pasos = [
    (EstadoAsignacion.aceptada,   'Aceptada'),
    (EstadoAsignacion.enCamino,   'En camino'),
    (EstadoAsignacion.enServicio, 'Trabajando'),
    (EstadoAsignacion.completada, 'Listo'),
  ];

  int get _indiceActual {
    return _pasos.indexWhere((p) => p.$1 == estado);
  }

  @override
  Widget build(BuildContext context) {
    // Solo mostramos la barra si el estado es uno de los pasos normales
    final idx = _indiceActual;
    if (idx == -1) return const SizedBox.shrink();

    return Row(
      children: List.generate(_pasos.length * 2 - 1, (i) {
        if (i.isOdd) {
          // Línea conectora
          final paso = i ~/ 2;
          return Expanded(
            child: Container(
              height: 2,
              color: paso < idx ? AppTheme.primario : Colors.grey.shade300,
            ),
          );
        }

        final paso = i ~/ 2;
        final activo = paso <= idx;
        return Column(
          children: [
            CircleAvatar(
              radius: 14,
              backgroundColor:
                  activo ? AppTheme.primario : Colors.grey.shade300,
              child: Icon(
                activo ? Icons.check : Icons.circle,
                size: 14,
                color: activo ? Colors.white : Colors.grey,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              _pasos[paso].$2,
              style: TextStyle(
                fontSize: 9,
                color: activo ? AppTheme.primario : AppTheme.textoSecundario,
                fontWeight:
                    paso == idx ? FontWeight.bold : FontWeight.normal,
              ),
            ),
          ],
        );
      }),
    );
  }
}

// ─── Widget auxiliar: fila con ícono ────────────────────────────────────────
class _Fila extends StatelessWidget {
  final IconData icon;
  final String texto;
  const _Fila({required this.icon, required this.texto});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(icon, size: 16, color: AppTheme.textoSecundario),
          const SizedBox(width: 8),
          Expanded(
              child: Text(texto,
                  style: const TextStyle(
                      color: AppTheme.textoSecundario, fontSize: 13))),
        ],
      ),
    );
  }
}


// ─── Card: servicio completado ───────────────────────────────────────────────
class _CardServicioCompletado extends StatelessWidget {
  final ServicioRealizado servicio;
  final Pago?             pago;
  final VoidCallback      onPagar;

  const _CardServicioCompletado({
    required this.servicio,
    required this.pago,
    required this.onPagar,
  });

  @override
  Widget build(BuildContext context) {

    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.task_alt, color: AppTheme.exito),
                const SizedBox(width: 8),
                const Text('Servicio completado',
                    style:
                        TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                const Spacer(),
                Chip(
                  label: Text(
                    'Bs. ${servicio.costoFinal.toStringAsFixed(2)}',
                    style: const TextStyle(
                        color: AppTheme.exito, fontWeight: FontWeight.bold),
                  ),
                  backgroundColor: AppTheme.exito.withValues(alpha: 0.12),
                  side: BorderSide.none,
                ),
              ],
            ),

            const Divider(height: 24),
            _Fila(icon: Icons.build_outlined,    texto: servicio.tipoServicio),
            _Fila(icon: Icons.description_outlined, texto: servicio.descripcionTrabajo),
            if (servicio.observaciones != null)
              _Fila(icon: Icons.notes_outlined, texto: servicio.observaciones!),
            const SizedBox(height: 16),

            if (pago == null)
              FilledButton.icon(
                onPressed: onPagar,
                icon: const Icon(Icons.payment),
                label: const Text('Registrar pago'),
                style: FilledButton.styleFrom(
                  minimumSize: const Size.fromHeight(46),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12)),
                ),
              )
            else
              Row(
                children: [
                  const Icon(Icons.check_circle, color: AppTheme.exito, size: 20),
                  const SizedBox(width: 8),
                  Text(
                    'Pago registrado (${pago!.estado == EstadoPago.pagado ? 'confirmado' : 'pendiente de confirmación'})',
                    style: const TextStyle(color: AppTheme.textoSecundario),
                  ),
                ],
              ),
          ],
        ),
      ),
    );
  }
}

// ─── Botón calificar ─────────────────────────────────────────────────────────
class _BotonCalificar extends StatelessWidget {
  final int          servicioId;
  final VoidCallback onCalificado;

  const _BotonCalificar({
    required this.servicioId,
    required this.onCalificado,
  });

  @override
  Widget build(BuildContext context) {
    return OutlinedButton.icon(
      onPressed: () =>
          _mostrarDialogoCalificacion(context, servicioId, onCalificado),
      icon: const Icon(Icons.star_outline),
      label: const Text('Calificar al mecánico'),
      style: OutlinedButton.styleFrom(
        minimumSize: const Size.fromHeight(46),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        foregroundColor: AppTheme.acento,
        side: const BorderSide(color: AppTheme.acento),
      ),
    );
  }

  void _mostrarDialogoCalificacion(
      BuildContext context, int servicioId, VoidCallback onCalificado) {
    int puntuacion = 5;
    final comentarioCtrl = TextEditingController();
    final service = CalificacionService();

    showDialog(
      context: context,
      builder: (dialogCtx) {
        return StatefulBuilder(
          builder: (dialogCtx, setDialogState) {
            return AlertDialog(
              title: const Text('Calificar servicio'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text('¿Cómo fue el servicio?',
                      style: TextStyle(color: AppTheme.textoSecundario)),
                  const SizedBox(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: List.generate(5, (i) {
                      final estrella = i + 1;
                      return GestureDetector(
                        onTap: () =>
                            setDialogState(() => puntuacion = estrella),
                        child: Icon(
                          estrella <= puntuacion
                              ? Icons.star_rounded
                              : Icons.star_outline_rounded,
                          color: AppTheme.acento,
                          size: 36,
                        ),
                      );
                    }),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: comentarioCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Comentario (opcional)',
                      border: OutlineInputBorder(),
                    ),
                    maxLines: 2,
                  ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(dialogCtx),
                  child: const Text('Cancelar'),
                ),
                FilledButton(
                  onPressed: () async {
                    Navigator.pop(dialogCtx);
                    try {
                      await service.calificar(
                        servicioId: servicioId,
                        puntuacion: puntuacion,
                        comentario: comentarioCtrl.text.trim(),
                      );
                      onCalificado();
                    } catch (_) {
                      // Silencioso; el usuario puede reintentar con pull-to-refresh
                    }
                  },
                  style: FilledButton.styleFrom(
                      backgroundColor: AppTheme.acento),
                  child: const Text('Enviar'),
                ),
              ],
            );
          },
        );
      },
    );
  }
}



// ─── Card: calificación ya enviada ──────────────────────────────────────────
class _CardCalificacion extends StatelessWidget {
  final Calificacion calificacion;
  const _CardCalificacion({required this.calificacion});

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.star_rounded, color: AppTheme.acento),
                SizedBox(width: 8),
                Text('Tu calificación',
                    style: TextStyle(
                        fontWeight: FontWeight.bold, fontSize: 15)),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: List.generate(
                5,
                (i) => Icon(
                  i < calificacion.puntuacion
                      ? Icons.star_rounded
                      : Icons.star_outline_rounded,
                  color: AppTheme.acento,
                  size: 28,
                ),
              ),
            ),
            if (calificacion.comentario != null &&
                calificacion.comentario!.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                calificacion.comentario!,
                style: const TextStyle(
                    color: AppTheme.textoSecundario, fontSize: 13),
              ),
            ],
          ],
        ),
      ),
    );
  }
}



// ─── Card: evidencias (fotos para la IA) ────────────────────────────────────
class _CardEvidencias extends StatelessWidget {
  final int incidenteId;
  const _CardEvidencias({required this.incidenteId});

  Future<void> _agregar(BuildContext context) async {
    final img = await ImagePicker().pickImage(
      source: ImageSource.gallery,
      maxWidth: 1280,
      imageQuality: 80,
    );
    if (img == null || !context.mounted) return;
    context.read<EvidenciaCubit>().subirFoto(incidenteId, img.path);
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                const Icon(Icons.photo_library_outlined,
                    color: AppTheme.primario),
                const SizedBox(width: 8),
                const Text('Fotos del problema',
                    style:
                        TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                const Spacer(),
                TextButton.icon(
                  onPressed: () => _agregar(context),
                  icon: const Icon(Icons.add_a_photo_outlined, size: 18),
                  label: const Text('Agregar'),
                ),
              ],
            ),
            const SizedBox(height: 8),
            BlocConsumer<EvidenciaCubit, EvidenciaState>(
              listener: (context, state) {
                if (state is EvidenciaError) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(state.mensaje),
                      backgroundColor: AppTheme.peligro,
                    ),
                  );
                }
              },
              builder: (context, state) {
                if (state is EvidenciaCargando) {
                  return const Center(child: CircularProgressIndicator());
                }
                final fotos =
                    state is EvidenciasListas ? state.lista : <Evidencia>[];
                if (fotos.isEmpty) {
                  return const Text(
                    'Agrega fotos para que la IA analice el problema.',
                    style: TextStyle(
                        color: AppTheme.textoSecundario, fontSize: 13),
                  );
                }
                return GridView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  gridDelegate:
                      const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 3,
                    crossAxisSpacing: 6,
                    mainAxisSpacing: 6,
                  ),
                  itemCount: fotos.length,
                  itemBuilder: (_, i) => ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: Image.network(
                      fotos[i].urlArchivo,
                      fit: BoxFit.cover,
                    ),
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
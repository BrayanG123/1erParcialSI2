import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:movil/config/routes.dart';
import 'package:movil/config/theme.dart';
import 'package:movil/features/auth/bloc/auth_cubit.dart';
import 'package:movil/features/auth/bloc/auth_state.dart';
import 'package:movil/features/mecanico/bloc/asignacion_cubit.dart';
import 'package:movil/features/mecanico/bloc/asignacion_state.dart';
import 'package:movil/models/asignacion_servicio.dart';


class HomeMecanicoScreen extends StatelessWidget {
  const HomeMecanicoScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => AsignacionCubit()..cargarMisAsignaciones(),
      child: const _HomeMecanicoView(),
    );
  }
}


class _HomeMecanicoView extends StatelessWidget {

  const _HomeMecanicoView();

  @override
  Widget build(BuildContext context) {
    final authState = context.watch<AuthCubit>().state;
    final nombre = authState is AuthAuthenticated
        ? authState.usuario.nombre
        : 'Mecánico';

    return Scaffold(
      backgroundColor: AppTheme.fondo,
      appBar: AppBar(
        title: Text('Hola, $nombre'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Cerrar sesión',
            onPressed: () => context.read<AuthCubit>().logout(),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => context.read<AsignacionCubit>().cargarMisAsignaciones(),
        child: BlocBuilder<AsignacionCubit, AsignacionState>(
          builder: (context, state) {
            if (state is AsignacionCargando) {
              return const Center(child: CircularProgressIndicator());
            }

            if (state is AsignacionError) {
              return Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.error_outline,
                        size: 48, color: AppTheme.peligro),
                    const SizedBox(height: 12),
                    Text(state.mensaje,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                            color: AppTheme.textoSecundario)),
                    const SizedBox(height: 16),
                    TextButton(
                      onPressed: () => context
                          .read<AsignacionCubit>()
                          .cargarMisAsignaciones(),
                      child: const Text('Reintentar'),
                    ),
                  ],
                ),
              );
            }

            if (state is AsignacionListaCargada) {
              if (state.asignaciones.isEmpty) {
                return const Center(
                  child: Text(
                    'No tienes asignaciones por el momento.',
                    style: TextStyle(color: AppTheme.textoSecundario),
                  ),
                );
              }

              // Separa activas e historial (el mecánico no gestiona el estado 'pendiente')
              final activas = state.asignaciones
                  .where((a) =>
                      a.estado == EstadoAsignacion.aceptada ||
                      a.estado == EstadoAsignacion.enCamino ||
                      a.estado == EstadoAsignacion.enServicio)
                  .toList();
              final historial = state.asignaciones
                  .where((a) =>
                      a.estado == EstadoAsignacion.completada ||
                      a.estado == EstadoAsignacion.cancelada)
                  .toList();

              return ListView(
                padding: const EdgeInsets.symmetric(vertical: 8),
                children: [
                  if (activas.isNotEmpty) ...[
                    _Seccion(titulo: 'En curso (${activas.length})'),
                    ...activas.map(
                      (a) => _TarjetaAsignacion(
                        asignacion: a,
                        onTap: () => context.push(
                          AppRoutes.detalleAsignacion,
                          extra: a.id,
                        ),
                      ),
                    ),
                  ],
                  if (historial.isNotEmpty) ...[
                    const _Seccion(titulo: 'Historial'),
                    ...historial.map(
                      (a) => _TarjetaAsignacion(
                        asignacion: a,
                        onTap: () => context.push(
                          AppRoutes.detalleAsignacion,
                          extra: a.id,
                        ),
                      ),
                    ),
                  ],
                ],
              );
            }

            return const SizedBox.shrink();
          },
        ),
      ),
    );
  }
}

class _Seccion extends StatelessWidget {
  final String titulo;
  const _Seccion({required this.titulo});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
      child: Text(
        titulo,
        style: const TextStyle(
          fontWeight: FontWeight.bold,
          fontSize: 15,
          color: AppTheme.primario,
        ),
      ),
    );
  }
}


class _TarjetaAsignacion extends StatelessWidget {
  final AsignacionServicio asignacion;
  final VoidCallback onTap;

  const _TarjetaAsignacion({
    required this.asignacion,
    required this.onTap,
  });

  static const _colores = {
    EstadoAsignacion.pendiente:   AppTheme.advertencia,
    EstadoAsignacion.aceptada:    AppTheme.primarioClaro,
    EstadoAsignacion.enCamino:    AppTheme.primario,
    EstadoAsignacion.enServicio:  AppTheme.acento,
    EstadoAsignacion.completada:  AppTheme.exito,
    EstadoAsignacion.rechazada:   AppTheme.textoSecundario,
    EstadoAsignacion.cancelada:   AppTheme.peligro,
  };

  static const _etiquetas = {
    EstadoAsignacion.pendiente:   'Pendiente',
    EstadoAsignacion.aceptada:    'Aceptada',
    EstadoAsignacion.enCamino:    'En camino',
    EstadoAsignacion.enServicio:  'En servicio',
    EstadoAsignacion.completada:  'Completada',
    EstadoAsignacion.rechazada:   'Rechazada',
    EstadoAsignacion.cancelada:   'Cancelada',
  };

  @override
  Widget build(BuildContext context) {
    final color    = _colores[asignacion.estado]    ?? AppTheme.textoSecundario;
    final etiqueta = _etiquetas[asignacion.estado]  ?? asignacion.estado.name;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 5),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        onTap: onTap,
        leading: CircleAvatar(
          backgroundColor: color.withValues(alpha:  0.15),
          child: Icon(Icons.build_circle, color: color),
        ),
        title: Text('Solicitud #${asignacion.id}'),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Incidente #${asignacion.incidenteId}',
              style: const TextStyle(fontSize: 12),
            ),
            if (asignacion.distanciaKm != null)
              Text(
                '${asignacion.distanciaKm!.toStringAsFixed(1)} km',
                style: const TextStyle(fontSize: 12),
              ),
          ],
        ),
        trailing: Chip(
          label: Text(
            etiqueta,
            style: TextStyle(color: color, fontSize: 11),
          ),
          backgroundColor: color.withValues(alpha:  0.12),
          side: BorderSide.none,
          padding: EdgeInsets.zero,
        ),
      ),
    );
  }
}
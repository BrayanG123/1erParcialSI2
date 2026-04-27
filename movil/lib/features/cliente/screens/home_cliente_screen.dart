import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:movil/config/routes.dart';
import 'package:movil/config/theme.dart';
import 'package:movil/features/auth/bloc/auth_cubit.dart';
import 'package:movil/features/auth/bloc/auth_state.dart';
import 'package:movil/features/cliente/bloc/incidente_cubit.dart';
import 'package:movil/features/cliente/bloc/incidente_state.dart';
import 'package:movil/models/incidente.dart';


class HomeClienteScreen extends StatelessWidget {
  const HomeClienteScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => IncidenteCubit()..cargarMisIncidentes(),
      child: const _HomeClienteView(),
    );
  }
}


class _HomeClienteView extends StatelessWidget {
  const _HomeClienteView();

  @override
  Widget build(BuildContext context) {
    final authState = context.watch<AuthCubit>().state;
    final nombre = authState is AuthAuthenticated
        ? authState.usuario.nombre
        : 'Cliente';

    return Scaffold(
      backgroundColor: AppTheme.fondo,
      appBar: AppBar(
        title: Text('Hola, $nombre'),
        actions: [
          IconButton(
            icon: const Icon(Icons.directions_car_outlined),
            tooltip: 'Mis vehículos',
            onPressed: () => context.push(AppRoutes.vehiculosPath),
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Cerrar sesión',
            onPressed: () => context.read<AuthCubit>().logout(),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => context.read<IncidenteCubit>().cargarMisIncidentes(),
        child: BlocBuilder<IncidenteCubit, IncidenteState>(
          builder: (context, state) {
            return CustomScrollView(
              slivers: [
                // --- Banner "Solicitar auxilio" ---
                SliverToBoxAdapter(
                  child: _BannerAuxilio(
                    onTap: () => context.push(AppRoutes.solicitarAuxilio),
                  ),
                ),

                // --- Título historial ---
                const SliverToBoxAdapter(
                  child: Padding(
                    padding: EdgeInsets.fromLTRB(20, 24, 20, 8),
                    child: Text(
                      'Mis solicitudes recientes',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),

                // --- Lista de incidentes ---
                if (state is IncidenteCargando)
                  const SliverFillRemaining(
                    child: Center(child: CircularProgressIndicator()),
                  )
                else if (state is IncidenteError)
                  SliverFillRemaining(
                    child: Center(
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
                        ],
                      ),
                    ),
                  )
                else if (state is IncidenteListaCargada &&
                    state.incidentes.isEmpty)
                  const SliverFillRemaining(
                    child: Center(
                      child: Text(
                        'Aún no tienes solicitudes.\nPresiona el botón para pedir auxilio.',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: AppTheme.textoSecundario),
                      ),
                    ),
                  )
                else if (state is IncidenteListaCargada)
                  SliverList(
                    delegate: SliverChildBuilderDelegate(
                      (context, i) =>
                          _TarjetaIncidente(incidente: state.incidentes[i]),
                      childCount: state.incidentes.length,
                    ),
                  )
                else
                  const SliverToBoxAdapter(child: SizedBox.shrink()),
              ],
            );
          },
        ),
      ),
    );
  }
}


// --- Widget: banner "Solicitar auxilio" ---
class _BannerAuxilio extends StatelessWidget {
  final VoidCallback onTap;

  const _BannerAuxilio({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppTheme.primario, AppTheme.primarioClaro],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: AppTheme.primario.withValues(alpha:  0.4),
            blurRadius: 12,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(20),
        child: InkWell(
          borderRadius: BorderRadius.circular(20),
          onTap: onTap,
          child: const Padding(
            padding: EdgeInsets.symmetric(horizontal: 28, vertical: 32),
            child: Row(
              children: [
                Icon(Icons.car_crash, size: 52, color: Colors.white),
                SizedBox(width: 20),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Solicitar auxilio',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      SizedBox(height: 6),
                      Text(
                        'Un mecánico llegará a tu ubicación.',
                        style: TextStyle(
                          color: Colors.white70,
                          fontSize: 13,
                        ),
                      ),
                    ],
                  ),
                ),
                Icon(Icons.arrow_forward_ios, color: Colors.white70, size: 18),
              ],
            ),
          ),
        ),
      ),
    );
  }
}


// --- Widget: tarjeta de incidente en el historial ---
class _TarjetaIncidente extends StatelessWidget {
  final Incidente incidente;

  const _TarjetaIncidente({required this.incidente});

  Color get _colorEstado {
    switch (incidente.estado) {
      case EstadoIncidente.disponible:
        return AppTheme.advertencia;
      case EstadoIncidente.noDisponible:
        return AppTheme.textoSecundario;
    }
  }

  String get _etiquetaEstado {
    switch (incidente.estado) {
      case EstadoIncidente.disponible:
        return 'Pendiente';
      case EstadoIncidente.noDisponible:
        return 'Atendido';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 6),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: _colorEstado.withValues(alpha:  0.15),
          child: Icon(Icons.directions_car, color: _colorEstado),
        ),
        title: Text(
          incidente.descripcion,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        subtitle: Text(
          '${incidente.fechaHora.day}/${incidente.fechaHora.month}/${incidente.fechaHora.year}',
          style: const TextStyle(fontSize: 12),
        ),
        trailing: Chip(
          label: Text(
            _etiquetaEstado,
            style: TextStyle(color: _colorEstado, fontSize: 12),
          ),
          backgroundColor: _colorEstado.withValues(alpha:  0.12),
          side: BorderSide.none,
          padding: EdgeInsets.zero,
        ),
      ),
    );
  }
}
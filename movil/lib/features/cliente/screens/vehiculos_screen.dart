import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:movil/config/routes.dart';
import 'package:movil/config/theme.dart';
import 'package:movil/features/cliente/bloc/vehiculo_cubit.dart';
import 'package:movil/features/cliente/bloc/vehiculo_state.dart';
import 'package:movil/models/vehiculo.dart';



class VehiculosScreen extends StatelessWidget {
  const VehiculosScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => VehiculoCubit()..cargarVehiculos(),
      child: const _VehiculosView(),
    );
  }
}


class _VehiculosView extends StatelessWidget {

  const _VehiculosView();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.fondo,
      appBar: AppBar(title: const Text('Mis vehículos')),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          // Esperamos que la pantalla de formulario haga pop con true si guardó
          final guardado = await context.push<bool>(
            '${AppRoutes.vehiculosPath}/nuevo',
          );
          if (guardado == true && context.mounted) {
            context.read<VehiculoCubit>().cargarVehiculos();
          }
        },
        backgroundColor: AppTheme.primario,
        child: const Icon(Icons.add),
      ),

      body: BlocConsumer<VehiculoCubit, VehiculoState>(
        listener: (context, state) {
          if (state is VehiculoEliminado) {
            context.read<VehiculoCubit>().cargarVehiculos();
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('Vehículo eliminado.'),
                backgroundColor: AppTheme.exito,
              ),
            );
          } else if (state is VehiculoError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.mensaje),
                backgroundColor: AppTheme.peligro,
              ),
            );
          }
        },
        builder: (context, state) {
          if (state is VehiculoCargando) {
            return const Center(child: CircularProgressIndicator());
          }

          if (state is VehiculoError) {
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
                  ElevatedButton(
                    onPressed: () =>
                        context.read<VehiculoCubit>().cargarVehiculos(),
                    child: const Text('Reintentar'),
                  ),
                ],
              ),
            );
          }

          if (state is VehiculoListaCargada && state.vehiculos.isEmpty) {
            return const Center(
              child: Text(
                'Aún no tienes vehículos.\nPresiona + para agregar uno.',
                textAlign: TextAlign.center,
                style: TextStyle(color: AppTheme.textoSecundario),
              ),
            );
          }

          final lista = state is VehiculoListaCargada ? state.vehiculos : <Vehiculo>[];

          return RefreshIndicator(
            onRefresh: () =>
                context.read<VehiculoCubit>().cargarVehiculos(),
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: lista.length,
              itemBuilder: (context, i) => _TarjetaVehiculo(
                vehiculo: lista[i],
                onEditar: () async {
                  final guardado = await context.push<bool>(
                    '${AppRoutes.vehiculosPath}/${lista[i].id}/editar',
                    extra: lista[i],
                  );
                  if (guardado == true && context.mounted) {
                    context.read<VehiculoCubit>().cargarVehiculos();
                  }
                },
                onEliminar: () =>
                    _confirmarEliminar(context, lista[i]),
              ),
            ),
          );
        },
      ),
    );
  }

  Future<void> _confirmarEliminar(
      BuildContext context, Vehiculo vehiculo) async {
    final confirmar = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Eliminar vehículo'),
        content: Text(
            '¿Eliminar ${vehiculo.placa} — ${vehiculo.modelo}?\nEsta acción no se puede deshacer.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
                backgroundColor: AppTheme.peligro),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Eliminar'),
          ),
        ],
      ),
    );
    if (confirmar == true && context.mounted) {
      context.read<VehiculoCubit>().eliminar(vehiculo.id);
    }
  }
}


class _TarjetaVehiculo extends StatelessWidget {

  final Vehiculo vehiculo;
  final VoidCallback onEditar;
  final VoidCallback onEliminar;

  const _TarjetaVehiculo({
    required this.vehiculo,
    required this.onEditar,
    required this.onEliminar,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape:
          RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),

      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(
            horizontal: 16, vertical: 8),
        leading: ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: vehiculo.fotoVehiculo != null
              ? Image.network(
                  // El backend guarda la ruta local; para el emulador usar baseUrl
                  'http://10.0.2.2:8000/${vehiculo.fotoVehiculo}',
                  width: 56,
                  height: 56,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => _iconoCarro(),
                )
              : _iconoCarro(),
        ),
        title: Text(
          '${vehiculo.placa} — ${vehiculo.modelo}',
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Text(
          vehiculo.color +
              (vehiculo.tipoSeguro != null
                  ? ' · Seguro: ${vehiculo.tipoSeguro}'
                  : ''),
          style: const TextStyle(
              color: AppTheme.textoSecundario, fontSize: 12),
        ),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            IconButton(
              icon: const Icon(Icons.edit_outlined),
              color: AppTheme.primario,
              onPressed: onEditar,
            ),
            IconButton(
              icon: const Icon(Icons.delete_outline),
              color: AppTheme.peligro,
              onPressed: onEliminar,
            ),
          ],
        ),

      ),
    );
  }

  Widget _iconoCarro() => Container(
        width: 56,
        height: 56,
        decoration: BoxDecoration(
          color: AppTheme.primario.withValues(alpha:  0.1),
          borderRadius: BorderRadius.circular(8),
        ),
        child: const Icon(Icons.directions_car,
            color: AppTheme.primario, size: 30),
      );
}
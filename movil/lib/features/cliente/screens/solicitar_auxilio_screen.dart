import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:movil/config/theme.dart';
import 'package:movil/features/auth/bloc/auth_cubit.dart';
import 'package:movil/features/auth/bloc/auth_state.dart';
import 'package:movil/features/cliente/bloc/incidente_cubit.dart';
import 'package:movil/features/cliente/bloc/incidente_state.dart';
import 'package:movil/models/categoria.dart';
import 'package:movil/models/vehiculo.dart';


class SolicitarAuxilioScreen extends StatelessWidget {
  const SolicitarAuxilioScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => IncidenteCubit()..cargarDatosFormulario(),
      child: const _SolicitarAuxilioView(),
    );
  }
}

class _SolicitarAuxilioView extends StatefulWidget {
  const _SolicitarAuxilioView();

  @override
  State<_SolicitarAuxilioView> createState() => _SolicitarAuxilioViewState();
}

class _SolicitarAuxilioViewState extends State<_SolicitarAuxilioView> {
  final _formKey        = GlobalKey<FormState>();
  final _descripcionCtrl = TextEditingController();
  final _latCtrl        = TextEditingController();
  final _lonCtrl        = TextEditingController();

  Vehiculo?  _vehiculoSeleccionado;
  Categoria? _categoriaSeleccionada;

  @override
  void dispose() {
    _descripcionCtrl.dispose();
    _latCtrl.dispose();
    _lonCtrl.dispose();
    super.dispose();
  }

  void _submit(BuildContext context) {
    if (!_formKey.currentState!.validate()) return;

    final authState = context.read<AuthCubit>().state;
    if (authState is! AuthAuthenticated) return;

    final lat = double.tryParse(_latCtrl.text.trim());
    final lon = double.tryParse(_lonCtrl.text.trim());
    if (lat == null || lon == null) return;

    context.read<IncidenteCubit>().crearIncidente(
      descripcion: _descripcionCtrl.text.trim(),
      latitud:     lat,
      longitud:    lon,
      clienteId:   authState.usuario.id,
      vehiculoId:  _vehiculoSeleccionado?.id,
      categoriaId: _categoriaSeleccionada?.id,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.fondo,
      appBar: AppBar(title: const Text('Solicitar auxilio')),
      body: BlocConsumer<IncidenteCubit, IncidenteState>(
        listener: (context, state) {
          if (state is IncidenteCreado) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('¡Auxilio solicitado! Buscando mecánico...'),
                backgroundColor: AppTheme.exito,
              ),
            );
            context.pop(); // vuelve al home del cliente
          } else if (state is IncidenteError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.mensaje),
                backgroundColor: AppTheme.peligro,
              ),
            );
          }
        },
        builder: (context, state) {
          if (state is IncidenteCargando && state is! IncidenteDatosCargados) {
            return const Center(child: CircularProgressIndicator());
          }

          final cargandoEnvio = state is IncidenteCargando;

          List<Vehiculo>  vehiculos  = [];
          List<Categoria> categorias = [];
          if (state is IncidenteDatosCargados) {
            vehiculos  = state.vehiculos;
            categorias = state.categorias;
          }

          return SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // --- Descripción ---
                  TextFormField(
                    controller: _descripcionCtrl,
                    maxLines: 3,
                    decoration: InputDecoration(
                      labelText: 'Describe el problema',
                      hintText: 'Ej. El carro no enciende, hay humo...',
                      border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12)),
                      alignLabelWithHint: true,
                    ),
                    validator: (v) => v == null || v.trim().isEmpty
                        ? 'Describe el problema'
                        : null,
                  ),
                  const SizedBox(height: 16),

                  // --- Vehículo (opcional) ---
                  if (vehiculos.isNotEmpty) ...[
                    DropdownButtonFormField<Vehiculo>(
                      value: _vehiculoSeleccionado,
                      decoration: InputDecoration(
                        labelText: 'Vehículo (opcional)',
                        border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12)),
                      ),
                      items: vehiculos
                          .map((v) => DropdownMenuItem(
                                value: v,
                                child: Text('${v.placa} — ${v.modelo}'),
                              ))
                          .toList(),
                      onChanged: (v) =>
                          setState(() => _vehiculoSeleccionado = v),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // --- Categoría (opcional) ---
                  if (categorias.isNotEmpty) ...[
                    DropdownButtonFormField<Categoria>(
                      value: _categoriaSeleccionada,
                      decoration: InputDecoration(
                        labelText: 'Categoría (opcional)',
                        border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12)),
                      ),
                      items: categorias
                          .map((c) => DropdownMenuItem(
                                value: c,
                                child: Text(c.nombre),
                              ))
                          .toList(),
                      onChanged: (c) =>
                          setState(() => _categoriaSeleccionada = c),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // --- Coordenadas manuales ---
                  // En la lección 09 esto se reemplaza con el mapa
                  const Text(
                    'Ubicación (coordenadas)',
                    style: TextStyle(
                        fontWeight: FontWeight.w600, fontSize: 14),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'En la lección 09 esto se obtendrá automáticamente del GPS.',
                    style: TextStyle(
                        fontSize: 12, color: AppTheme.textoSecundario),
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      Expanded(
                        child: TextFormField(
                          controller: _latCtrl,
                          keyboardType: const TextInputType.numberWithOptions(
                              decimal: true, signed: true),
                          decoration: InputDecoration(
                            labelText: 'Latitud',
                            hintText: '-17.7833',
                            border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(12)),
                          ),
                          validator: (v) {
                            if (v == null || v.trim().isEmpty)
                              return 'Requerido';
                            if (double.tryParse(v.trim()) == null)
                              return 'Número inválido';
                            return null;
                          },
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: TextFormField(
                          controller: _lonCtrl,
                          keyboardType: const TextInputType.numberWithOptions(
                              decimal: true, signed: true),
                          decoration: InputDecoration(
                            labelText: 'Longitud',
                            hintText: '-63.1821',
                            border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(12)),
                          ),
                          validator: (v) {
                            if (v == null || v.trim().isEmpty)
                              return 'Requerido';
                            if (double.tryParse(v.trim()) == null)
                              return 'Número inválido';
                            return null;
                          },
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 28,),

                  // --- Botón enviar ---
                  FilledButton.icon(
                    onPressed: cargandoEnvio ? null : () => _submit(context),
                    style: FilledButton.styleFrom(
                      backgroundColor: AppTheme.acento,
                      minimumSize: const Size.fromHeight(52),
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12)),
                    ),
                    icon: cargandoEnvio
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(
                                strokeWidth: 2.5, color: Colors.white),
                          )
                        : const Icon(Icons.send),
                    label: const Text('Solicitar auxilio',
                        style: TextStyle(fontSize: 16)),
                  ),
                ],

              ),
            ),
          );
        },
      ),
    );
  }
}
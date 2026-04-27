import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:movil/config/theme.dart';
import 'package:movil/features/auth/bloc/auth_cubit.dart';
import 'package:movil/features/auth/bloc/auth_state.dart';
import 'package:movil/features/cliente/bloc/incidente_cubit.dart';
import 'package:movil/features/cliente/bloc/incidente_state.dart';
import 'package:movil/features/cliente/widgets/mapa_selector.dart';
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

  Vehiculo?  _vehiculoSeleccionado;
  Categoria? _categoriaSeleccionada;

  // Coordenadas elegidas en el mapa
  double? _latitud;
  double? _longitud;

  @override
  void dispose() {
    _descripcionCtrl.dispose();
    super.dispose();
  }

  void _submit(BuildContext context) {
    if (!_formKey.currentState!.validate()) return;

    if (_latitud == null || _longitud == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Marca tu ubicación en el mapa.'),
          backgroundColor: AppTheme.advertencia,
        ),
      );
      return;
    }

    final authState = context.read<AuthCubit>().state;
    if (authState is! AuthAuthenticated) return;

    context.read<IncidenteCubit>().crearIncidente(
      descripcion: _descripcionCtrl.text.trim(),
      latitud:     _latitud!,
      longitud:    _longitud!,
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
            padding: const EdgeInsets.all(20),
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
                    'Tu ubicacion',
                    style: TextStyle(
                        fontWeight: FontWeight.w600, fontSize: 14),
                  ),
                  const SizedBox(height: 4),

                  // Muestra las coordenadas elegidas (o instrucción)
                  if (_latitud != null && _longitud != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 6),
                      child: Text(
                        'Lat: ${_latitud!.toStringAsFixed(6)}'
                        '  |  Lon: ${_longitud!.toStringAsFixed(6)}',
                        style: const TextStyle(
                            fontSize: 12,
                            color: AppTheme.textoSecundario),
                      ),
                    ) else
                    const Padding(
                      padding: EdgeInsets.only(bottom: 6),
                      child: Text(
                        'Toca el mapa o usa el botón GPS para marcar tu posición.',
                        style: TextStyle(
                            fontSize: 12,
                            color: AppTheme.textoSecundario),
                      ),
                    ),

                  // Mapa de 300 px de alto
                  ClipRRect(
                    borderRadius: BorderRadius.circular(12),
                    child: SizedBox(
                      height: 300,
                      child: MapaSelector(
                        onPosicionSeleccionada: (lat, lon) {
                          setState(() {
                            _latitud  = lat;
                            _longitud = lon;
                          });
                        },
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),


                  // --- Botón enviar ---
                  FilledButton.icon(
                    onPressed: cargandoEnvio 
                        ? null 
                        : () => _submit(context),
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
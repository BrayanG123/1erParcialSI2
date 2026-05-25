import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:image_picker/image_picker.dart';
import 'package:movil/config/theme.dart';
import 'package:movil/features/cliente/bloc/vehiculo_cubit.dart';
import 'package:movil/features/cliente/bloc/vehiculo_state.dart';
import 'package:movil/models/vehiculo.dart';



class FormVehiculoScreen extends StatelessWidget {
  /// Si es null → modo creación. Si tiene valor → modo edición.
  final Vehiculo? vehiculo;

  const FormVehiculoScreen({super.key, this.vehiculo});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => VehiculoCubit(),
      child: _FormVehiculoView(vehiculo: vehiculo),
    );
  }
}


class _FormVehiculoView extends StatefulWidget {
  final Vehiculo? vehiculo;

  const _FormVehiculoView({this.vehiculo});

  @override
  State<_FormVehiculoView> createState() => _FormVehiculoViewState();
}


class _FormVehiculoViewState extends State<_FormVehiculoView> {

  final _formKey    = GlobalKey<FormState>();
  late final TextEditingController _placaCtrl;
  late final TextEditingController _modeloCtrl;
  late final TextEditingController _colorCtrl;
  late final TextEditingController _seguroCtrl;

  File? _fotoSeleccionada;

  bool get _esEdicion => widget.vehiculo != null;

  @override
  void initState() {
    super.initState();
    _placaCtrl  = TextEditingController(text: widget.vehiculo?.placa  ?? '');
    _modeloCtrl = TextEditingController(text: widget.vehiculo?.modelo ?? '');
    _colorCtrl  = TextEditingController(text: widget.vehiculo?.color  ?? '');
    _seguroCtrl = TextEditingController(
        text: widget.vehiculo?.tipoSeguro ?? '');
  }

  @override
  void dispose() {
    _placaCtrl.dispose();
    _modeloCtrl.dispose();
    _colorCtrl.dispose();
    _seguroCtrl.dispose();
    super.dispose();
  }

  Future<void> _elegirFoto() async {
    final picker = ImagePicker();
    final imagen = await picker.pickImage(
      source: ImageSource.gallery,
      maxWidth: 1024,
      maxHeight: 1024,
      imageQuality: 80,
    );
    if (imagen != null && mounted) {
      setState(() => _fotoSeleccionada = File(imagen.path));
    }
  }

  void _submit(BuildContext context) {
    if (!_formKey.currentState!.validate()) return;

    if (_esEdicion) {
      context.read<VehiculoCubit>().actualizar(
            id: widget.vehiculo!.id,
            modelo: _modeloCtrl.text.trim(),
            color: _colorCtrl.text.trim(),
            tipoSeguro: _seguroCtrl.text.trim().isEmpty
                ? null
                : _seguroCtrl.text.trim(),
            rutaFoto: _fotoSeleccionada?.path,
          );
    } else {
      context.read<VehiculoCubit>().crear(
            placa:      _placaCtrl.text.trim(),
            modelo:     _modeloCtrl.text.trim(),
            color:      _colorCtrl.text.trim(),
            tipoSeguro: _seguroCtrl.text.trim().isEmpty
                ? null
                : _seguroCtrl.text.trim(),
            rutaFoto: _fotoSeleccionada?.path,
          );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.fondo,
      appBar: AppBar(
        title: Text(_esEdicion ? 'Editar vehículo' : 'Nuevo vehículo'),
      ),
      body: BlocListener<VehiculoCubit, VehiculoState> (
        listener: (context, state) {
          if (state is VehiculoGuardado) {
            // Devolver true al pop para que la lista sepa que debe recargarse
            Navigator.of(context).pop(true);
          } else if (state is VehiculoError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.mensaje),
                backgroundColor: AppTheme.peligro,
              ),
            );
          }
        },
        child: BlocBuilder<VehiculoCubit, VehiculoState>(
          builder: (context, state) {
            final cargando = state is VehiculoCargando;
            
            return SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // ── Foto ───
                    Center(
                      child: GestureDetector(
                        onTap: _elegirFoto,
                        child: Stack(
                          children: [
                            ClipRRect(
                              borderRadius: BorderRadius.circular(12),
                              child: _fotoSeleccionada != null
                                  ? Image.file(
                                      _fotoSeleccionada!,
                                      width: 140,
                                      height: 100,
                                      fit: BoxFit.cover,
                                    )
                                  : Container(
                                      width: 140,
                                      height: 100,
                                      color: AppTheme.primario
                                          .withValues(alpha: 0.08),
                                      child: const Icon(
                                        Icons.directions_car,
                                        size: 48,
                                        color: AppTheme.primario,
                                      ),
                                    ),
                            ),
                            Positioned(
                              bottom: 4,
                              right: 4,
                              child: Container(
                                decoration: const BoxDecoration(
                                  color: AppTheme.primario,
                                  shape: BoxShape.circle,
                                ),
                                padding: const EdgeInsets.all(4),
                                child: const Icon(Icons.camera_alt,
                                    color: Colors.white, size: 16),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),

                    const SizedBox(height: 4),
                    const Center(
                      child: Text(
                        'Toca para agregar foto (opcional)',
                        style: TextStyle(
                            fontSize: 11,
                            color: AppTheme.textoSecundario),
                      ),
                    ),
                    const SizedBox(height: 20),

                     // ── Placa (solo en creación) ───
                    if (!_esEdicion) ...[
                      _Campo(
                        controller: _placaCtrl,
                        label: 'Placa',
                        hint: 'ABC-1234',
                        validator: (v) => v == null || v.trim().isEmpty
                            ? 'Ingresa la placa'
                            : null,
                      ),
                      const SizedBox(height: 14),
                    ],

                    // ── Modelo ───────────────────────────────────────────
                    _Campo(
                      controller: _modeloCtrl,
                      label: 'Modelo',
                      hint: 'Toyota Corolla 2020',
                      validator: (v) => v == null || v.trim().isEmpty
                          ? 'Ingresa el modelo'
                          : null,
                    ),
                    const SizedBox(height: 14),

                    // ── Color ────────────────────────────────────────────
                    _Campo(
                      controller: _colorCtrl,
                      label: 'Color',
                      hint: 'Blanco',
                      validator: (v) => v == null || v.trim().isEmpty
                          ? 'Ingresa el color'
                          : null,
                    ),
                    const SizedBox(height: 14),

                    // ── Tipo de seguro (opcional) ────────────────────────
                    _Campo(
                      controller: _seguroCtrl,
                      label: 'Tipo de seguro (opcional)',
                      hint: 'SOAT',
                    ),
                    const SizedBox(height: 28),

                    // ── Botón guardar ─────────────────────────────────────
                    FilledButton(
                      onPressed:
                          cargando ? null : () => _submit(context),
                      style: FilledButton.styleFrom(
                        backgroundColor: AppTheme.primario,
                        minimumSize: const Size.fromHeight(52),
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12)),
                      ),
                      child: cargando
                          ? const SizedBox(
                              height: 22,
                              width: 22,
                              child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white),
                            )
                          : Text(
                              _esEdicion
                                  ? 'Guardar cambios'
                                  : 'Agregar vehículo',
                              style: const TextStyle(fontSize: 16),
                            ),
                    ),
                  ],
                ),
              ),
            );
          }
        )
      )
    );
  }
}


// Widget auxiliar para campos de texto
class _Campo extends StatelessWidget {
  final TextEditingController controller;
  final String label;
  final String? hint;
  final String? Function(String?)? validator;

  const _Campo({
    required this.controller,
    required this.label,
    this.hint,
    this.validator,
  });

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        border:
            OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
      ),
      validator: validator,
    );
  }
}
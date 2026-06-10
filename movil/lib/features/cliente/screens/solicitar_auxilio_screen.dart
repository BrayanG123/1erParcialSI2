import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:movil/config/theme.dart';
import 'package:movil/features/auth/bloc/auth_cubit.dart';
import 'package:movil/features/auth/bloc/auth_state.dart';
import 'package:movil/features/cliente/bloc/incidente_cubit.dart';
import 'package:movil/features/cliente/bloc/incidente_state.dart';
import 'package:movil/features/cliente/screens/seleccionar_ubicacion_screen.dart';
import 'package:movil/models/categoria.dart';
import 'package:movil/models/vehiculo.dart';
import 'dart:io';
import 'package:image_picker/image_picker.dart';
import 'package:record/record.dart';
import 'package:permission_handler/permission_handler.dart';


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
  File? _foto;

  // Audio (solo se guarda el path; la lógica vive en _AudioGrabacion)
  String? _rutaAudio;

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
      rutaFoto:    _foto?.path,   
      rutaAudio:   _rutaAudio,
    );
  }

  Future<void> _abrirSelectorUbicacion() async {
    final resultado = await Navigator.push<(double, double)>(
      context,
      MaterialPageRoute(
        builder: (_) => SeleccionarUbicacionScreen(
          latitudInicial:  _latitud,
          longitudInicial: _longitud,
        ),
      ),
    );
    if (resultado != null && mounted) {
      setState(() {
        _latitud  = resultado.$1;
        _longitud = resultado.$2;
      });
    }
  }

  Future<void> _elegirFoto() async {
    final fuente = await showModalBottomSheet<ImageSource>(
      context: context,
      builder: (_) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.camera_alt_outlined,
                  color: Color(0xFF1565C0)),
              title: const Text('Tomar foto con cámara'),
              onTap: () => Navigator.pop(context, ImageSource.camera),
            ),
            ListTile(
              leading: const Icon(Icons.photo_library_outlined,
                  color: Color(0xFF1565C0)),
              title: const Text('Elegir de galería'),
              onTap: () => Navigator.pop(context, ImageSource.gallery),
            ),
          ],
        ),
      ),
    );

    if (fuente == null) return;

    final picker = ImagePicker();
    final imagen = await picker.pickImage(
      source: fuente,
      maxWidth: 1024,
      maxHeight: 1024,
      imageQuality: 80,
    );
    if (imagen != null && mounted) {
      setState(() => _foto = File(imagen.path));
    }
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
          } 

          if (state is IncidenteGuardadoOffline) {
            // Mostrar mensaje claro al usuario
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Row(
                  children: [
                    const Icon(Icons.wifi_off, color: Colors.white),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Sin conexión. Tu solicitud se guardó localmente '
                        'y se enviará cuando haya internet. '
                        '(${state.totalPendientes} pendiente(s))',
                      ),
                    ),
                  ],
                ),
                backgroundColor: Colors.orange.shade700,
                duration: const Duration(seconds: 6),
                behavior: SnackBarBehavior.floating,
              ),
            );
            // Volver a la pantalla anterior (misma experiencia que cuando hay internet)
            context.pop();
          } 
          
          if (state is IncidenteError) {
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

                  // --- Ubicación ---
                  const Text(
                    'Tu ubicación',
                    style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                  ),
                  const SizedBox(height: 8),
                  if (_latitud != null && _longitud != null)
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 12),
                      decoration: BoxDecoration(
                        color: AppTheme.primario.withValues(alpha: 0.06),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                            color: AppTheme.primario.withValues(alpha: 0.3)),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.location_on,
                              color: AppTheme.primario),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              'Lat: ${_latitud!.toStringAsFixed(6)}\n'
                              'Lon: ${_longitud!.toStringAsFixed(6)}',
                              style: const TextStyle(
                                  fontSize: 12,
                                  color: AppTheme.textoSecundario),
                            ),
                          ),
                          TextButton(
                            onPressed: _abrirSelectorUbicacion,
                            child: const Text('Cambiar'),
                          ),
                        ],
                      ),
                    )
                  else
                    OutlinedButton.icon(
                      onPressed: _abrirSelectorUbicacion,
                      icon: const Icon(Icons.map_outlined),
                      label: const Text('Seleccionar ubicación en el mapa'),
                      style: OutlinedButton.styleFrom(
                        minimumSize: const Size.fromHeight(48),
                        foregroundColor: AppTheme.primario,
                        side: const BorderSide(color: AppTheme.primario),
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12)),
                      ),
                    ),
                  const SizedBox(height: 24),

                  const SizedBox(height: 8),
                  const Text(
                    'Foto del problema (opcional)',
                    style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                  ),
                  const SizedBox(height: 8),
                  GestureDetector(
                    onTap: _elegirFoto,
                    child: Container(
                      height: 130,
                      decoration: BoxDecoration(
                        color: AppTheme.primario.withValues(alpha: 0.06),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: AppTheme.primario.withValues(alpha: 0.3),
                          width: 1.5,
                        ),
                      ),
                      child: _foto != null
                          ? ClipRRect(
                              borderRadius: BorderRadius.circular(11),
                              child: Image.file(
                                _foto!,
                                fit: BoxFit.cover,
                                width: double.infinity,
                              ),
                            )
                          : const Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(Icons.add_a_photo_outlined,
                                    size: 36, color: AppTheme.primario),
                                SizedBox(height: 6),
                                Text(
                                  'Toca para agregar una foto',
                                  style: TextStyle(
                                      color: AppTheme.textoSecundario, fontSize: 13),
                                ),
                              ],
                            ),
                    ),
                  ),
                  // Si hay foto, mostrar botón para quitarla
                  if (_foto != null)
                    Align(
                      alignment: Alignment.centerRight,
                      child: TextButton.icon(
                        onPressed: () => setState(() => _foto = null),
                        icon: const Icon(Icons.close, size: 16, color: AppTheme.peligro),
                        label: const Text('Quitar foto',
                            style: TextStyle(color: AppTheme.peligro, fontSize: 12)),
                      ),
                    ),
                  const SizedBox(height: 16),


                  // ─── Audio descriptivo ──
                  const Text(
                    'Audio descriptivo (opcional)',
                    style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                  ),
                  const SizedBox(height: 8),
                  _AudioGrabacion(
                    onAudioGrabado:  (path) => setState(() => _rutaAudio = path),
                    onAudioEliminado: ()    => setState(() => _rutaAudio = null),
                  ),
                  const SizedBox(height: 16),


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


// ─── Widget de grabación de audio (versión mínima, sin timer) ───────────────

class _AudioGrabacion extends StatefulWidget {
  final void Function(String path) onAudioGrabado;
  final VoidCallback onAudioEliminado;

  const _AudioGrabacion({
    required this.onAudioGrabado,
    required this.onAudioEliminado,
  });

  @override
  State<_AudioGrabacion> createState() => _AudioGrabacionState();
}

class _AudioGrabacionState extends State<_AudioGrabacion> {
  final AudioRecorder _recorder = AudioRecorder();
  String? _rutaAudio;
  bool _grabando = false;

  @override
  void dispose() {
    _recorder.dispose();
    super.dispose();
  }

  Future<void> _grabar() async {
    final permiso = await Permission.microphone.request();
    if (!permiso.isGranted) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Permiso de micrófono denegado.')),
        );
      }
      return;
    }
    final path =
        '${Directory.systemTemp.path}/audio_${DateTime.now().millisecondsSinceEpoch}.m4a';
    await _recorder.start(const RecordConfig(encoder: AudioEncoder.aacLc), path: path);
    if (mounted) setState(() => _grabando = true);
  }

  Future<void> _detener() async {
    final path = await _recorder.stop();
    if (mounted) {
      setState(() {
        _grabando = false;
        _rutaAudio = path;
      });
      if (path != null) widget.onAudioGrabado(path);
    }
  }

  void _eliminar() {
    if (_rutaAudio != null) {
      final f = File(_rutaAudio!);
      if (f.existsSync()) f.deleteSync();
    }
    setState(() {
      _rutaAudio = null;
      _grabando = false;
    });
    widget.onAudioEliminado();
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        // Botón grabar
        IconButton.filled(
          onPressed: _grabando ? null : _grabar,
          icon: const Icon(Icons.mic),
          tooltip: 'Iniciar grabación',
          style: IconButton.styleFrom(
            backgroundColor: _grabando
                ? Colors.grey.shade300
                : const Color(0xFF1565C0),
            foregroundColor: Colors.white,
          ),
        ),
        const SizedBox(width: 8),
        // Botón detener
        IconButton.filled(
          onPressed: _grabando ? _detener : null,
          icon: const Icon(Icons.stop),
          tooltip: 'Detener grabación',
          style: IconButton.styleFrom(
            backgroundColor: _grabando
                ? const Color(0xFFC62828)
                : Colors.grey.shade300,
            foregroundColor: Colors.white,
          ),
        ),
        const SizedBox(width: 12),
        // Estado / nombre de archivo
        Expanded(
          child: Text(
            _grabando
                ? 'Grabando...'
                : _rutaAudio != null
                    ? 'Audio listo'
                    : 'Sin audio',
            style: TextStyle(
              fontSize: 13,
              color: _grabando
                  ? const Color(0xFFC62828)
                  : _rutaAudio != null
                      ? const Color(0xFF2E7D32)
                      : AppTheme.textoSecundario,
            ),
          ),
        ),
        // Botón eliminar (solo si hay audio)
        if (_rutaAudio != null && !_grabando)
          IconButton(
            onPressed: _eliminar,
            icon: const Icon(Icons.delete_outline, color: Color(0xFFC62828)),
            tooltip: 'Eliminar audio',
          ),
      ],
    );
  }
}
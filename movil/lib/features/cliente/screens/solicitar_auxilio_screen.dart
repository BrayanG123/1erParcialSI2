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
import 'dart:io';
import 'package:image_picker/image_picker.dart';
import 'dart:async';
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

  // Audio
  final AudioRecorder _recorder = AudioRecorder();
  String? _rutaAudio;           // path del archivo grabado
  bool    _grabando = false;
  int     _segundos = 0;
  Timer?  _timer;

  @override
  void dispose() {
    _descripcionCtrl.dispose();
    _timer?.cancel();
    _recorder.dispose(); 
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

  Future<void> _iniciarGrabacion() async {
    // Solicitar permiso de micrófono
    final permiso = await Permission.microphone.request();
    if (!permiso.isGranted) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Permiso de micrófono denegado'),
            backgroundColor: Color(0xFFC62828),
          ),
        );
      }
      return;
    }

    final path =
        '${Directory.systemTemp.path}/audio_incidente_${DateTime.now().millisecondsSinceEpoch}.m4a';

    await _recorder.start(
      const RecordConfig(encoder: AudioEncoder.aacLc),
      path: path,
    );

    setState(() {
      _grabando = true;
      _segundos = 0;
    });

    // Contador de segundos
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() => _segundos++);
    });
  }

  Future<void> _detenerGrabacion() async {
    _timer?.cancel();
    final path = await _recorder.stop();
    setState(() {
      _grabando  = false;
      _rutaAudio = path;
    });
  }

  void _eliminarAudio() {
    if (_rutaAudio != null) {
      final archivo = File(_rutaAudio!);
      if (archivo.existsSync()) archivo.deleteSync();
    }
    setState(() {
      _rutaAudio = null;
      _grabando  = false;
      _segundos  = 0;
    });
  }

  String _formatearTiempo(int segundos) {
    final min = segundos ~/ 60;
    final seg = segundos % 60;
    return '${min.toString().padLeft(2, '0')}:${seg.toString().padLeft(2, '0')}';
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
                  _WidgetGrabacion(
                    grabando:    _grabando,
                    rutaAudio:   _rutaAudio,
                    segundos:    _segundos,
                    formatear:   _formatearTiempo,
                    onIniciar:   _iniciarGrabacion,
                    onDetener:   _detenerGrabacion,
                    onEliminar:  _eliminarAudio,
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


// ─── Widget de grabación de audio ──────────────────────────────────────────

class _WidgetGrabacion extends StatelessWidget {
  final bool     grabando;
  final String?  rutaAudio;
  final int      segundos;
  final String   Function(int) formatear;
  final VoidCallback onIniciar;
  final VoidCallback onDetener;
  final VoidCallback onEliminar;

  const _WidgetGrabacion({
    required this.grabando,
    required this.rutaAudio,
    required this.segundos,
    required this.formatear,
    required this.onIniciar,
    required this.onDetener,
    required this.onEliminar,
  });

  @override
  Widget build(BuildContext context) {
    // Estado: audio ya grabado
    if (rutaAudio != null && !grabando) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: const Color(0xFF2E7D32).withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
              color: const Color(0xFF2E7D32).withValues(alpha: 0.4)),
        ),
        child: Row(
          children: [
            const Icon(Icons.check_circle_outline,
                color: Color(0xFF2E7D32)),
            const SizedBox(width: 10),
            const Expanded(
              child: Text(
                'Audio grabado',
                style: TextStyle(
                    color: Color(0xFF2E7D32),
                    fontWeight: FontWeight.w500),
              ),
            ),
            IconButton(
              icon: const Icon(Icons.delete_outline,
                  color: Color(0xFFC62828)),
              tooltip: 'Eliminar audio',
              onPressed: onEliminar,
            ),
          ],
        ),
      );
    }

    // Estado: grabando
    if (grabando) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: const Color(0xFFC62828).withValues(alpha: 0.06),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
              color: const Color(0xFFC62828).withValues(alpha: 0.4)),
        ),
        child: Row(
          children: [
            const Icon(Icons.fiber_manual_record,
                color: Color(0xFFC62828), size: 14),
            const SizedBox(width: 8),
            Text(
              'Grabando  ${formatear(segundos)}',
              style: const TextStyle(
                  color: Color(0xFFC62828),
                  fontWeight: FontWeight.w500),
            ),
            const Spacer(),
            ElevatedButton.icon(
              onPressed: onDetener,
              icon: const Icon(Icons.stop, size: 18),
              label: const Text('Detener'),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFC62828),
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(
                    horizontal: 14, vertical: 8),
              ),
            ),
          ],
        ),
      );
    }

    // Estado: sin audio
    return OutlinedButton.icon(
      onPressed: onIniciar,
      icon: const Icon(Icons.mic_outlined),
      label: const Text('Grabar audio descriptivo'),
      style: OutlinedButton.styleFrom(
        minimumSize: const Size.fromHeight(48),
        foregroundColor: const Color(0xFF1565C0),
        side: const BorderSide(color: Color(0xFF1565C0)),
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12)),
      ),
    );
  }
}
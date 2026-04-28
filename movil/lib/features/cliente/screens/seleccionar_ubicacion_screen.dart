import 'package:flutter/material.dart';
import 'package:movil/config/theme.dart';
import 'package:movil/features/cliente/widgets/mapa_selector.dart';

/// Pantalla independiente para elegir ubicación en el mapa.
///
/// Devuelve un record `(double latitud, double longitud)` cuando el usuario
/// confirma, o `null` si cancela (pulsando la flecha atrás).
///
/// Uso:
/// ```dart
/// final resultado = await Navigator.push<(double, double)>(
///   context,
///   MaterialPageRoute(builder: (_) => const SeleccionarUbicacionScreen()),
/// );
/// if (resultado != null) { /* usar resultado.$1 y resultado.$2 */ }
/// ```
class SeleccionarUbicacionScreen extends StatefulWidget {
  /// Coordenadas previas para pre-posicionar el marcador (opcional).
  final double? latitudInicial;
  final double? longitudInicial;

  const SeleccionarUbicacionScreen({
    super.key,
    this.latitudInicial,
    this.longitudInicial,
  });

  @override
  State<SeleccionarUbicacionScreen> createState() =>
      _SeleccionarUbicacionScreenState();
}

class _SeleccionarUbicacionScreenState
    extends State<SeleccionarUbicacionScreen> {
  double? _latitud;
  double? _longitud;

  @override
  void initState() {
    super.initState();
    _latitud  = widget.latitudInicial;
    _longitud = widget.longitudInicial;
  }

  @override
  Widget build(BuildContext context) {
    final tieneUbicacion = _latitud != null && _longitud != null;

    return Scaffold(
      backgroundColor: AppTheme.fondo,
      appBar: AppBar(
        title: const Text('Seleccionar ubicación'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context), // cancela sin devolver nada
        ),
      ),
      body: Column(
        children: [
          // Instrucción
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            color: AppTheme.primario.withValues(alpha: 0.07),
            child: Row(
              children: const [
                Icon(Icons.info_outline, size: 16, color: AppTheme.primario),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Toca el mapa para marcar tu posición o usa el botón GPS.',
                    style: TextStyle(fontSize: 13, color: AppTheme.primario),
                  ),
                ),
              ],
            ),
          ),

          // Mapa — ocupa todo el espacio disponible
          Expanded(
            child: MapaSelector(
              posicionInicial: null, // MapaSelector ya pide GPS en initState
              onPosicionSeleccionada: (lat, lon) {
                setState(() {
                  _latitud  = lat;
                  _longitud = lon;
                });
              },
            ),
          ),

          // Panel inferior con coordenadas + botón confirmar
          SafeArea(
            child: Container(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
              decoration: BoxDecoration(
                color: AppTheme.fondo,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.08),
                    blurRadius: 8,
                    offset: const Offset(0, -2),
                  ),
                ],
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Coordenadas seleccionadas
                  if (tieneUbicacion)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.location_on,
                              size: 16, color: AppTheme.acento),
                          const SizedBox(width: 6),
                          Text(
                            'Lat: ${_latitud!.toStringAsFixed(6)}'
                            '   Lon: ${_longitud!.toStringAsFixed(6)}',
                            style: const TextStyle(
                              fontSize: 12,
                              color: AppTheme.textoSecundario,
                            ),
                          ),
                        ],
                      ),
                    ),

                  // Botón confirmar
                  FilledButton.icon(
                    onPressed: tieneUbicacion
                        ? () => Navigator.pop(context, (_latitud!, _longitud!))
                        : null,
                    icon: const Icon(Icons.check),
                    label: const Text('Confirmar ubicación'),
                    style: FilledButton.styleFrom(
                      backgroundColor: AppTheme.acento,
                      minimumSize: const Size.fromHeight(52),
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

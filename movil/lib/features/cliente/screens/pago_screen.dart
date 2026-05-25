import 'package:flutter/material.dart';
import 'package:movil/config/theme.dart';
// import 'package:movil/features/cliente/services/calificacion_service.dart';
import 'package:movil/features/cliente/services/pago_service.dart';
import 'package:movil/models/pago.dart';
import 'package:movil/models/servicio_realizado.dart';


class PagoScreen extends StatefulWidget {
  final ServicioRealizado servicio;
  final VoidCallback onPagoRegistrado; // callback para recargar la pantalla anterior

  const PagoScreen({
    super.key,
    required this.servicio,
    required this.onPagoRegistrado,
  });

  @override
  State<PagoScreen> createState() => _PagoScreenState();
}


class _PagoScreenState extends State<PagoScreen>{

  final _pagoService = PagoService();
  MetodoPago _metodo = MetodoPago.efectivo;
  bool _cargando = false;
  String? _error;

  Future<void> _pagar() async {
    setState(() {
      _cargando = true;
      _error    = null;
    });
    try {
      await _pagoService.registrarPago(
        servicioId: widget.servicio.id,
        metodo:     _metodo,
      );
      if (!mounted) return;
      widget.onPagoRegistrado();
      Navigator.of(context).pop();
    } catch (e) {
      setState(() {
        _error   = e.toString();
        _cargando = false;
      });
    }
  }

  @override
  Widget build(BuildContext context){
    return Scaffold(
      backgroundColor: AppTheme.fondo,
      appBar: AppBar(title: const Text('Registrar pago')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [

            // ── Resumen del servicio ──────────────────────────────────────
            Card(
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16)),
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.build_circle_outlined,
                            color: AppTheme.primario),
                        SizedBox(width: 8),
                        Text('Resumen del servicio',
                            style: TextStyle(
                                fontWeight: FontWeight.bold, fontSize: 15)),
                      ],
                    ),
                    const Divider(height: 24),
                    _Fila('Tipo',        widget.servicio.tipoServicio),
                    _Fila('Descripción', widget.servicio.descripcionTrabajo),
                    if (widget.servicio.observaciones != null)
                      _Fila('Observaciones', widget.servicio.observaciones!),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // ── Monto ─────────────────────────────────────────────────────
            Card(
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16)),
              color: AppTheme.primario.withValues(alpha: 0.06),
              child: Padding(
                padding: const EdgeInsets.symmetric(
                    horizontal: 24, vertical: 20),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Total a pagar',
                        style: TextStyle(fontSize: 16)),
                    Text(
                      'Bs. ${widget.servicio.costoFinal.toStringAsFixed(2)}',
                      style: const TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.primario,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // ── Método de pago ────────────────────────────────────────────
            const Text('Método de pago',
                style:
                    TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
            const SizedBox(height: 12),
            _TarjetaMetodo(
              metodo:     MetodoPago.efectivo,
              titulo:     'Efectivo',
              subtitulo:  'Paga en mano al mecánico',
              icono:      Icons.payments_outlined,
              seleccionado: _metodo == MetodoPago.efectivo,
              onTap: () => setState(() => _metodo = MetodoPago.efectivo),
            ),

            const SizedBox(height: 10),
            _TarjetaMetodo(
              metodo:     MetodoPago.pasarela,
              titulo:     'Pasarela de pago',
              subtitulo:  'QR / transferencia bancaria',
              icono:      Icons.qr_code_scanner_outlined,
              seleccionado: _metodo == MetodoPago.pasarela,
              onTap: () => setState(() => _metodo = MetodoPago.pasarela),
            ),
            const SizedBox(height: 32),

            if (_error != null) ...[
              Text(_error!,
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: AppTheme.peligro)),
              const SizedBox(height: 16),
            ],

            FilledButton.icon(
              onPressed: _cargando ? null : _pagar,
              icon: _cargando
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: Colors.white))
                  : const Icon(Icons.check_circle_outline),
              label: Text(_cargando ? 'Procesando…' : 'Confirmar pago'),
              style: FilledButton.styleFrom(
                minimumSize: const Size.fromHeight(52),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14)),
              ),
            ),
          ]
        ),
      )
    );
  }
}


class _TarjetaMetodo extends StatelessWidget {

  final MetodoPago metodo;
  final String     titulo;
  final String     subtitulo;
  final IconData   icono;
  final bool       seleccionado;
  final VoidCallback onTap;

  const _TarjetaMetodo({
    required this.metodo,
    required this.titulo,
    required this.subtitulo,
    required this.icono,
    required this.seleccionado,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: seleccionado ? AppTheme.primario : Colors.grey.shade300,
            width: seleccionado ? 2 : 1,
          ),
          color: seleccionado
              ? AppTheme.primario.withValues(alpha: 0.05)
              : null,
        ),
        child: Row(
          children: [
            Icon(icono,
                color: seleccionado
                    ? AppTheme.primario
                    : AppTheme.textoSecundario),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(titulo,
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        color: seleccionado ? AppTheme.primario : null,
                      )),
                  Text(subtitulo,
                      style: const TextStyle(
                          fontSize: 12,
                          color: AppTheme.textoSecundario)),
                ],
              ),
            ),
            if (seleccionado)
              const Icon(Icons.check_circle, color: AppTheme.primario),
          ],
        ),
      ),
    );
  }
}


class _Fila extends StatelessWidget {
  final String label;
  final String valor;
  const _Fila(this.label, this.valor);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(label,
                style: const TextStyle(
                    color: AppTheme.textoSecundario, fontSize: 13)),
          ),
          Expanded(
              child: Text(valor,
                  style: const TextStyle(fontWeight: FontWeight.w600))),
        ],
      ),
    );
  }
}
import 'dart:async';

import 'package:flutter/material.dart';
import 'package:movil/config/theme.dart';
import 'package:movil/features/cliente/services/pago_service.dart';
import 'package:movil/models/pago.dart';
import 'package:movil/models/servicio_realizado.dart';
import 'package:url_launcher/url_launcher.dart';


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

  // ── Estado del flujo Stripe ──
  int?   _pagoIdStripe;
  bool   _esperandoStripe = false;
  bool   _verificando     = false;
  Timer? _pollTimer;

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  Future<void> _pagar() async {
    // Pasarela = Stripe Checkout en el navegador
    if (_metodo == MetodoPago.pasarela) {
      await _pagarConStripe();
      return;
    }

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

  // ── Flujo Stripe ────────────────────────────────────────────────────

  Future<void> _pagarConStripe() async {
    setState(() {
      _cargando = true;
      _error    = null;
    });
    try {
      // 1. El backend crea el Pago pendiente + la Checkout Session
      final checkout = await _pagoService.crearCheckoutStripe(widget.servicio.id);
      _pagoIdStripe = checkout['pago_id'] as int;
      final url = Uri.parse(checkout['checkout_url'] as String);

      // 2. Abrir Stripe Checkout en el navegador externo
      final abierto = await launchUrl(url, mode: LaunchMode.externalApplication);
      if (!abierto) throw Exception('No se pudo abrir el navegador');

      // 3. Quedarse esperando la confirmación (polling al backend,
      //    que a su vez consulta a Stripe — no depende del webhook)
      if (!mounted) return;
      setState(() {
        _cargando        = false;
        _esperandoStripe = true;
      });
      _pollTimer?.cancel();
      _pollTimer = Timer.periodic(
        const Duration(seconds: 4),
        (_) => _verificarPagoStripe(silencioso: true),
      );
    } catch (e) {
      setState(() {
        _error    = e.toString();
        _cargando = false;
      });
    }
  }

  Future<void> _verificarPagoStripe({bool silencioso = false}) async {
    if (_pagoIdStripe == null || _verificando) return;
    _verificando = true;
    try {
      final pago = await _pagoService.confirmarPagoStripe(_pagoIdStripe!);
      if (pago.estado == EstadoPago.pagado) {
        _pollTimer?.cancel();
        if (!mounted) return;
        widget.onPagoRegistrado();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('¡Pago realizado exitosamente!'),
            backgroundColor: Colors.green,
          ),
        );
        Navigator.of(context).pop();
      } else if (!silencioso && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('El pago aún no se confirma. Completa el pago en el navegador.'),
            backgroundColor: Colors.orange,
          ),
        );
      }
    } catch (_) {
      // silencioso: reintenta en el próximo tick del timer
    } finally {
      _verificando = false;
    }
  }

  void _cancelarEsperaStripe() {
    _pollTimer?.cancel();
    setState(() => _esperandoStripe = false);
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
              titulo:     'Tarjeta de crédito/débito',
              subtitulo:  'Pago seguro con Stripe',
              icono:      Icons.credit_card,
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

            // ── Esperando confirmación de Stripe ─────────────────────────
            if (_esperandoStripe) ...[
              Card(
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16)),
                color: Colors.blue.shade50,
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    children: [
                      const SizedBox(
                        width: 28,
                        height: 28,
                        child: CircularProgressIndicator(strokeWidth: 3),
                      ),
                      const SizedBox(height: 16),
                      const Text(
                        'Esperando confirmación del pago…',
                        style: TextStyle(fontWeight: FontWeight.bold),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 6),
                      const Text(
                        'Completa el pago en el navegador.\n'
                        'Esta pantalla se actualizará sola al confirmarse.',
                        style: TextStyle(
                            fontSize: 12, color: AppTheme.textoSecundario),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 16),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          TextButton(
                            onPressed: _cancelarEsperaStripe,
                            child: const Text('Cancelar'),
                          ),
                          const SizedBox(width: 8),
                          FilledButton.tonal(
                            onPressed: () =>
                                _verificarPagoStripe(silencioso: false),
                            child: const Text('Ya pagué, verificar'),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ] else
              FilledButton.icon(
                onPressed: _cargando ? null : _pagar,
                icon: _cargando
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(
                            strokeWidth: 2, color: Colors.white))
                    : Icon(_metodo == MetodoPago.pasarela
                        ? Icons.credit_card
                        : Icons.check_circle_outline),
                label: Text(_cargando
                    ? 'Procesando…'
                    : (_metodo == MetodoPago.pasarela
                        ? 'Pagar con Stripe'
                        : 'Confirmar pago')),
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
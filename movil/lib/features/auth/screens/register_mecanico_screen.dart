import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:movil/config/routes.dart';
import 'package:movil/config/theme.dart';
import 'package:movil/features/auth/bloc/auth_cubit.dart';
import 'package:movil/features/auth/bloc/auth_state.dart';
import 'package:movil/features/auth/models/registro_mecanico_request.dart';
import 'package:movil/features/auth/widgets/auth_text_field.dart';


class RegisterMecanicoScreen extends StatefulWidget {
  const RegisterMecanicoScreen({super.key});

  @override
  State<RegisterMecanicoScreen> createState() => _RegisterMecanicoScreenState();
}


class _RegisterMecanicoScreenState extends State<RegisterMecanicoScreen> {
  final _formKey          = GlobalKey<FormState>();
  final _nombreCtrl       = TextEditingController();
  final _apellidoCtrl     = TextEditingController();
  final _emailCtrl        = TextEditingController();
  final _usernameCtrl     = TextEditingController();
  final _passwordCtrl     = TextEditingController();
  final _especialidadCtrl = TextEditingController();
  final _telefonoCtrl     = TextEditingController();
  final _tallerIdCtrl     = TextEditingController();
  bool _mostrarPassword   = false;

  @override
  void dispose() {
    _nombreCtrl.dispose();
    _apellidoCtrl.dispose();
    _emailCtrl.dispose();
    _usernameCtrl.dispose();
    _passwordCtrl.dispose();
    _especialidadCtrl.dispose();
    _telefonoCtrl.dispose();
    _tallerIdCtrl.dispose();
    super.dispose();
  }

  void _submit() {
    if (!_formKey.currentState!.validate()) return;
    final tallerId = int.tryParse(_tallerIdCtrl.text.trim());
    if (tallerId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('El ID del taller debe ser un número.'),
          backgroundColor: AppTheme.peligro,
        ),
      );
      return;
    }
    context.read<AuthCubit>().registrarMecanico(
      RegistroMecanicoRequest(
        nombre:       _nombreCtrl.text.trim(),
        apellido:     _apellidoCtrl.text.trim(),
        email:        _emailCtrl.text.trim(),
        username:     _usernameCtrl.text.trim(),
        password:     _passwordCtrl.text,
        especialidad: _especialidadCtrl.text.trim(),
        telefono:     _telefonoCtrl.text.trim(),
        tallerId:     tallerId,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.fondo,
      appBar: AppBar(title: const Text('Registro de mecánico')),
      body: BlocConsumer<AuthCubit, AuthState>(
        listener: (context, state) {
          if (state is AuthRegistroExitoso) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.mensaje),
                backgroundColor: AppTheme.exito,
                duration: const Duration(seconds: 4),
              ),
            );
            context.go(AppRoutes.login);
          } else if (state is AuthError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.mensaje),
                backgroundColor: AppTheme.peligro,
              ),
            );
          }
        },
        builder: (context, state) {
          final cargando = state is AuthLoading;
          return SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text(
                    'Datos personales',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                  ),
                  const SizedBox(height: 12),
                  AuthTextField(
                    controller: _nombreCtrl,
                    label: 'Nombre',
                    validator: (v) => v == null || v.trim().isEmpty
                        ? 'Ingresa tu nombre'
                        : null,
                  ),
                  const SizedBox(height: 14),
                  AuthTextField(
                    controller: _apellidoCtrl,
                    label: 'Apellido',
                    validator: (v) => v == null || v.trim().isEmpty
                        ? 'Ingresa tu apellido'
                        : null,
                  ),
                  const SizedBox(height: 14),
                  AuthTextField(
                    controller: _emailCtrl,
                    label: 'Correo electrónico',
                    keyboardType: TextInputType.emailAddress,
                    validator: (v) {
                      if (v == null || v.trim().isEmpty) return 'Ingresa tu correo';
                      if (!v.contains('@')) return 'Correo inválido';
                      return null;
                    },
                  ),
                  const SizedBox(height: 14),
                  AuthTextField(
                    controller: _usernameCtrl,
                    label: 'Nombre de usuario',
                    validator: (v) => v == null || v.trim().isEmpty
                        ? 'Ingresa un nombre de usuario'
                        : null,
                  ),
                  const SizedBox(height: 14),
                  AuthTextField(
                    controller: _passwordCtrl,
                    label: 'Contraseña',
                    obscureText: !_mostrarPassword,
                    textInputAction: TextInputAction.next,
                    suffixIcon: IconButton(
                      icon: Icon(
                        _mostrarPassword
                            ? Icons.visibility_off
                            : Icons.visibility,
                      ),
                      onPressed: () =>
                          setState(() => _mostrarPassword = !_mostrarPassword),
                    ),
                    validator: (v) {
                      if (v == null || v.isEmpty) return 'Ingresa una contraseña';
                      if (v.length < 6) return 'Mínimo 6 caracteres';
                      return null;
                    },
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    'Datos profesionales',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                  ),
                  const SizedBox(height: 12),
                  AuthTextField(
                    controller: _especialidadCtrl,
                    label: 'Especialidad',
                    hint: 'Ej. Mecánica general, Electricidad',
                    validator: (v) => v == null || v.trim().isEmpty
                        ? 'Ingresa tu especialidad'
                        : null,
                  ),
                  const SizedBox(height: 14),
                  AuthTextField(
                    controller: _telefonoCtrl,
                    label: 'Teléfono',
                    keyboardType: TextInputType.phone,
                    validator: (v) => v == null || v.trim().isEmpty
                        ? 'Ingresa tu teléfono'
                        : null,
                  ),
                  const SizedBox(height: 14),
                  AuthTextField(
                    controller: _tallerIdCtrl,
                    label: 'ID del taller',
                    hint: 'Ej. 1',
                    keyboardType: TextInputType.number,
                    textInputAction: TextInputAction.done,
                    validator: (v) {
                      if (v == null || v.trim().isEmpty) return 'Ingresa el ID del taller';
                      if (int.tryParse(v.trim()) == null) return 'Debe ser un número';
                      return null;
                    },
                  ),
                  const SizedBox(height: 28),
                  FilledButton(
                    onPressed: cargando ? null : _submit,
                    style: FilledButton.styleFrom(
                      backgroundColor: AppTheme.acento,
                      minimumSize: const Size.fromHeight(52),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: cargando
                        ? const SizedBox(
                            height: 22,
                            width: 22,
                            child: CircularProgressIndicator(
                              strokeWidth: 2.5,
                              color: Colors.white,
                            ),
                          )
                        : const Text(
                            'Enviar solicitud',
                            style: TextStyle(fontSize: 16),
                          ),
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
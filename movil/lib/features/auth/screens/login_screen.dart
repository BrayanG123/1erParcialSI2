import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:movil/config/routes.dart';
import 'package:movil/config/theme.dart';
import 'package:movil/features/auth/bloc/auth_cubit.dart';
import 'package:movil/features/auth/bloc/auth_state.dart';
import 'package:movil/features/auth/widgets/auth_text_field.dart';
import 'package:movil/models/rol_usuario.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _usernameCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  bool _mostrarPassword = false;


  @override
  void dispose() {
    _usernameCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  void _submit() {
    if (!_formKey.currentState!.validate()) return;
    context.read<AuthCubit>().login(
      _usernameCtrl.text.trim(),
      _passwordCtrl.text,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.fondo,
      body: BlocConsumer<AuthCubit, AuthState>(
        listener: (context, state) {
          if (state is AuthAuthenticated) {
            if (state.usuario.rol == RolUsuario.mecanico) {
              context.goNamed(AppRoutes.homeMecanico);
            } else {
              context.goNamed(AppRoutes.homeCliente);
            }
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

          return SafeArea(

            child: Center(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 28),
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      const Icon(
                        Icons.car_repair,
                        size: 72,
                        color: AppTheme.primario,
                      ),
                      const SizedBox(height: 12,),
                      const Text(
                        'Auxilio Vehicular',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontSize: 26,
                          fontWeight: FontWeight.bold,
                          color: AppTheme.primario,
                        ),
                      ),
                      const SizedBox(height: 8,),
                      const Text(
                        'Inicia sesión para continuar',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: AppTheme.textoSecundario),
                      ),
                      const SizedBox(height: 36,),

                      // -- username
                      AuthTextField(
                        controller: _usernameCtrl,
                        label: 'Usuario',
                        hint: 'tu_usuario',
                        validator: (v) =>
                            v == null || v.trim().isEmpty ? 'Ingresa tu usuario' : null,
                      ),
                      const SizedBox(height: 16),

                      // --- Contraseña ---
                      AuthTextField(
                        controller: _passwordCtrl,
                        label: 'Contraseña',
                        obscureText: !_mostrarPassword,
                        textInputAction: TextInputAction.done,
                        suffixIcon: IconButton(
                          icon: Icon(
                            _mostrarPassword
                                ? Icons.visibility_off
                                : Icons.visibility,
                          ),
                          onPressed: () =>
                              setState(() => _mostrarPassword = !_mostrarPassword),
                        ),
                        validator: (v) =>
                            v == null || v.isEmpty ? 'Ingresa tu contraseña' : null,
                      ),
                      const SizedBox(height: 28),

                      // --- Botón iniciar sesión ---
                      FilledButton(
                        onPressed: cargando ? null : _submit,
                        style: FilledButton.styleFrom(
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
                                'Iniciar sesión',
                                style: TextStyle(fontSize: 16),
                              ),
                      ),
                      const SizedBox(height: 20),

                      // --- Link a registro ---
                      TextButton(
                        onPressed: cargando
                            ? null
                            : () => context.push(AppRoutes.register),
                        child: const Text('¿No tienes cuenta? Regístrate'),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }

}
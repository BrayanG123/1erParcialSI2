import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:movil/config/routes.dart';
import 'package:movil/features/auth/bloc/auth_cubit.dart';
import 'package:movil/features/auth/bloc/auth_state.dart';
import 'package:movil/models/rol_usuario.dart';



class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocListener<AuthCubit, AuthState>(
      listener: (context, state) {
        if (state is AuthAuthenticated) {
          // Redirige según el rol del usuario
          if (state.usuario.rol == RolUsuario.mecanico) {
            context.goNamed(AppRoutes.homeMecanico);
          } else {
            context.goNamed(AppRoutes.homeCliente);
          } 
        } else if (state is AuthUnauthenticated) {
          context.goNamed(AppRoutes.login);
        }
        // AuthLoading: se queda en el splash
      },

      child: const Scaffold(
        backgroundColor: Color(0xFF1565C0),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.car_repair, size: 80, color: Colors.white),
              SizedBox(height: 24),
              Text(
                'Auxilio Vehicular',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                ),
              ),
              SizedBox(height: 48),
              CircularProgressIndicator(color: Colors.white),
            ],
          ),
        ),
      ),
    );
  }
}
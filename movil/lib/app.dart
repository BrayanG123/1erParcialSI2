import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:movil/config/theme.dart';
import 'package:movil/config/routes.dart';
import 'package:movil/features/auth/bloc/auth_cubit.dart';

class AuxilioApp extends StatelessWidget {
  const AuxilioApp({super.key});


  @override
  Widget build(BuildContext context) {

    return BlocProvider(
      create: (_) => AuthCubit()..verificarSesion(),
      child: MaterialApp.router(
        title: 'Auxilio Vehicular',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light,
        routerConfig: appRouter,
      ),
    );
  }
}
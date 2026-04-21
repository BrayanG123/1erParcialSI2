import 'package:flutter/material.dart';
import 'package:movil/config/theme.dart';
import 'package:movil/config/routes.dart';

class AuxilioApp extends StatelessWidget {
  const AuxilioApp({super.key});


  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Auxilio Vehicular',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      routerConfig: appRouter,
    );
  }
}
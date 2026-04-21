import 'package:flutter/material.dart';


class AuxilioApp extends StatelessWidget {
  const AuxilioApp({super.key});


  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Auxilio Vehicular',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF1565C0)),
        useMaterial3: true,
      ),
      home: const Scaffold(
        body: Center(
          child: Text('hola mundo'),
        ),
      ),
    );
  }
}
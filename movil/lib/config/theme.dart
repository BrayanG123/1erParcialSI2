import 'package:flutter/material.dart';



class AppTheme {

  // --- Paleta ---
  static const Color primario        = Color(0xFF1565C0); // azul oscuro
  static const Color primarioClaro   = Color(0xFF1E88E5); // azul medio
  static const Color acento          = Color(0xFFE65100); // naranja
  static const Color exito           = Color(0xFF2E7D32); // verde
  static const Color peligro         = Color(0xFFC62828); // rojo
  static const Color advertencia     = Color(0xFFF9A825); // amarillo
  static const Color fondo           = Color(0xFFF5F5F5); // gris muy claro
  static const Color superficie      = Color(0xFFFFFFFF);
  static const Color textoSecundario = Color(0xFF757575);


  static ThemeData get light {

    final base = ColorScheme.fromSeed(
      seedColor: primario,
      primary: primario,
      secondary: acento,
      surface: superficie,
      error: peligro,
      brightness: Brightness.light,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: base,
      scaffoldBackgroundColor: fondo,

      // AppBar
      appBarTheme: const AppBarTheme(
        backgroundColor: primario,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: TextStyle(
          color: Colors.white,
          fontSize: 18,
          fontWeight: FontWeight.w600,
        ),
      ),


      // Botones elevados
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primario,
          foregroundColor: Colors.white,
          minimumSize: const Size.fromHeight(48),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),


      // Botones de texto
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: primario,
        ),
      ),


      // Campos de texto
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFFBDBDBD)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFFBDBDBD)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: primario, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: peligro),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),


      // Cards
      cardTheme: CardThemeData(
        color: superficie,
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      ),


      // Chips
      chipTheme: ChipThemeData(
        backgroundColor: const Color(0xFFE3F2FD),
        labelStyle: const TextStyle(color: primario),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
      ),

    );
  }
}
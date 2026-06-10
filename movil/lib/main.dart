import 'package:firebase_core/firebase_core.dart'; 
import 'package:flutter/material.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:movil/app.dart';
import 'package:movil/features/cliente/services/offline_incidente_service.dart';



void main() async {
  // Necesario antes de cualquier llamada async en main()
  WidgetsFlutterBinding.ensureInitialized();

  // Inicializar Firebase PRIMERO (antes de Hive y runApp)
  await Firebase.initializeApp(); 

  // Inicializar Hive en el directorio de documentos de la app
  await Hive.initFlutter();

  // Abrir la caja de incidentes pendientes
  // Después de esto, OfflineIncidenteService puede usarse en cualquier parte
  await OfflineIncidenteService.init();
  
  runApp(const AuxilioApp());

}
import 'package:flutter_test/flutter_test.dart';
import 'package:movil/app.dart';

void main() {
  testWidgets('App arranca sin errores', (WidgetTester tester) async {
    await tester.pumpWidget(const AuxilioApp());
    // Solo verificamos que el widget raíz se construye sin lanzar errores.
    expect(tester.takeException(), isNull);
  });
}

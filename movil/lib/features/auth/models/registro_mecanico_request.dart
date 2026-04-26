class RegistroMecanicoRequest {
  final String nombre;
  final String apellido;
  final String email;
  final String username;
  final String password;
  final String especialidad;
  final String telefono;
  final int tallerId;

  const RegistroMecanicoRequest({
    required this.nombre,
    required this.apellido,
    required this.email,
    required this.username,
    required this.password,
    required this.especialidad,
    required this.telefono,
    required this.tallerId,
  });

  Map<String, dynamic> toJson() => {
    'nombre':       nombre,
    'apellido':     apellido,
    'email':        email,
    'username':     username,
    'password':     password,
    'especialidad': especialidad,
    'telefono':     telefono,
    'taller_id':    tallerId,
  };
}
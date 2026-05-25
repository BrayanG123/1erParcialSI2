class RegistroClienteRequest {
  final String nombre;
  final String apellido;
  final String email;
  final String username;
  final String password;

  const RegistroClienteRequest({
    required this.nombre,
    required this.apellido,
    required this.email,
    required this.username,
    required this.password,
  });

  Map<String, dynamic> toJson() => {
    'nombre':   nombre,
    'apellido': apellido,
    'email':    email,
    'username': username,
    'password': password,
  };
}
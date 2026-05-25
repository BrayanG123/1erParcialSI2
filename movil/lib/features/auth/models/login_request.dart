

class LoginRequest {

  final String username;
  final String password;

  const LoginRequest({required this.username, required this.password});

  /// FastAPI espera form-data para OAuth2: usa Map, no JSON
  Map<String, String> toFormData() => {
    'username': username,
    'password': password,
  };
  
}
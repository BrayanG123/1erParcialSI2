export interface LoginCredentials {
  email: string;
  password?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
}

export interface TokenPayload {
  sub: string;
  usuario_id: number;
  rol: string;
  exp: number;
}

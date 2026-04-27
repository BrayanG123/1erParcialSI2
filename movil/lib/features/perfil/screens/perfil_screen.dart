import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:movil/features/perfil/bloc/perfil_cubit.dart';
import 'package:movil/features/perfil/bloc/perfil_state.dart';
import 'package:movil/models/usuario_perfil.dart';


class PerfilScreen extends StatelessWidget {
  const PerfilScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => PerfilCubit()..cargar(),
      child: const _PerfilView(),
    );
  }
}


class _PerfilView extends StatelessWidget {
  const _PerfilView();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mi Perfil'),
        backgroundColor: const Color(0xFF1565C0),
        foregroundColor: Colors.white,
      ),
      body: BlocConsumer<PerfilCubit, PerfilState>(
        listener: (context, state) {
          if (state is PerfilGuardado) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('Perfil actualizado'),
                backgroundColor: Color(0xFF2E7D32),
              ),
            );
          }
          if (state is PasswordCambiado) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('Contraseña cambiada correctamente'),
                backgroundColor: Color(0xFF2E7D32),
              ),
            );
          }
          if (state is PerfilError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.mensaje),
                backgroundColor: const Color(0xFFC62828),
              ),
            );
          }
        },
        builder: (context, state) {
          if (state is PerfilCargando || state is PerfilInicial) {
            return const Center(child: CircularProgressIndicator());
          }

          UsuarioConPerfil? usuario;
          if (state is PerfilCargado) usuario = state.usuario;
          if (state is PerfilGuardado) usuario = state.usuario;

          if (usuario == null) {
            return Center(
              child: ElevatedButton(
                onPressed: () => context.read<PerfilCubit>().cargar(),
                child: const Text('Reintentar'),
              ),
            );
          }

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                _SeccionDatosPersonales(usuario: usuario),
                const SizedBox(height: 24),
                // const _SeccionCambiarPassword(),
              ],
            ),
          );
        },
      ),
    );
  }
}


// ─── Sección 1: editar datos personales ────────────────────────────────────
class _SeccionDatosPersonales extends StatefulWidget {
  final UsuarioConPerfil usuario;

  const _SeccionDatosPersonales({required this.usuario});

  @override
  State<_SeccionDatosPersonales> createState() =>
      _SeccionDatosPersonalesState();
}

class _SeccionDatosPersonalesState extends State<_SeccionDatosPersonales> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _nombre;
  late final TextEditingController _apellido;
  late final TextEditingController _username;

  @override
  void initState() {
    super.initState();
    _nombre   = TextEditingController(text: widget.usuario.nombre);
    _apellido = TextEditingController(text: widget.usuario.apellido);
    _username = TextEditingController(text: widget.usuario.username);
  }

  @override
  void dispose() {
    _nombre.dispose();
    _apellido.dispose();
    _username.dispose();
    super.dispose();
  }

  void _guardar() {
    if (!_formKey.currentState!.validate()) return;
    context.read<PerfilCubit>().guardar(
          nombre: _nombre.text.trim(),
          apellido: _apellido.text.trim(),
          username: _username.text.trim(),
        );
  }

  @override
  Widget build(BuildContext context) {
    final cargando = context.watch<PerfilCubit>().state is PerfilCargando;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Datos personales',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1565C0),
                ),
              ),
              const SizedBox(height: 8),
              // Email (solo lectura)
              TextFormField(
                initialValue: widget.usuario.email,
                readOnly: true,
                decoration: const InputDecoration(
                  labelText: 'Email',
                  prefixIcon: Icon(Icons.email_outlined),
                  helperText: 'El email no se puede cambiar',
                ),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _nombre,
                textCapitalization: TextCapitalization.words,
                decoration: const InputDecoration(
                  labelText: 'Nombre',
                  prefixIcon: Icon(Icons.person_outline),
                ),
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? 'Campo requerido' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _apellido,
                textCapitalization: TextCapitalization.words,
                decoration: const InputDecoration(
                  labelText: 'Apellido',
                  prefixIcon: Icon(Icons.person_outline),
                ),
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? 'Campo requerido' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _username,
                decoration: const InputDecoration(
                  labelText: 'Username',
                  prefixIcon: Icon(Icons.alternate_email),
                ),
                validator: (v) {
                  if (v == null || v.trim().isEmpty) return 'Campo requerido';
                  final regex = RegExp(r'^[a-zA-Z0-9_]{3,50}$');
                  if (!regex.hasMatch(v.trim())) {
                    return 'Solo letras, números y _ (3-50 caracteres)';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: cargando ? null : _guardar,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF1565C0),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                  ),
                  child: cargando
                      ? const SizedBox(
                          height: 18,
                          width: 18,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Text('Guardar cambios'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
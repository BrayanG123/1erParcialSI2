# Paquete de Inteligencia Artificial del sistema.
#
# Contiene tres motores independientes:
#   - clasificador_imagen.py   → visión artificial (CLIP) para clasificar fotos
#   - generador_resumen.py     → ficha estructurada del incidente (Gemma 2B vía Ollama)
#   - asignador_inteligente.py → selección del mejor taller (algoritmo de puntuación)
#
# DISEÑO PENSADO PARA HARDWARE LIMITADO:
#   - Ningún modelo se carga al iniciar el backend (carga perezosa).
#   - Si las librerías de IA no están instaladas, el backend arranca igual
#     y los endpoints devuelven un mensaje claro de qué falta.
#   - El generador de resumen SIEMPRE funciona: si Ollama no está corriendo,
#     usa una plantilla estructurada sin LLM.

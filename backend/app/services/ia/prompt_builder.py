from app.models.evidencia import Evidencia, TipoEvidencia



def construir_prompt(descripcion: str, evidencias: list[Evidencia]) -> str:
    fotos  = [e for e in evidencias if e.tipo == TipoEvidencia.foto]
    audios = [e for e in evidencias if e.tipo == TipoEvidencia.audio]

    lineas = [
        "Eres un asistente experto en diagnóstico de averías vehiculares.",
        "Analiza la siguiente información de un incidente de auxilio vehicular.",
        "",
        f"Descripción del cliente: {descripcion}",
    ]

    if fotos:
        lineas.append(f"Fotos adjuntas: {len(fotos)} imagen(es).")

    if audios:
        lineas.append(f"Audios adjuntos: {len(audios)} grabación(es).")

    lineas += [
        "",
        "Responde con un JSON con exactamente estas dos claves:",
        '{ "resumen": "descripción técnica breve del problema", '
        '"categoria_sugerida": "pinchazo | bateria | motor | frenos | otro" }',
        "No incluyas texto adicional fuera del JSON.",
    ]

    return "\n".join(lineas)
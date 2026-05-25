import requests
from app.config import settings


# Formatos de audio que acepta la REST API de Azure Speech
CONTENT_TYPES_SOPORTADOS = {
    "audio/wav": "audio/wav",
    "audio/wave": "audio/wav",
    "audio/x-wav": "audio/wav",
    "audio/ogg": "audio/ogg; codecs=opus",
    "audio/webm": "audio/webm; codecs=opus",
    # WAV es el más compatible y recomendado desde la app móvil
}


def transcribir_audio(audio_bytes: bytes, content_type: str = "audio/wav") -> str:
    """
    Transcribe audio a texto usando la REST API de Azure Speech to Text.

    Args:
        audio_bytes: contenido binario del archivo de audio.
        content_type: MIME type del audio ("audio/wav", "audio/ogg", etc.).

    Returns:
        Texto transcrito. Cadena vacía si no se detectó voz.

    Raises:
        RuntimeError: si Azure devuelve un error HTTP o la clave no está configurada.
    """
    if not settings.AZURE_SPEECH_KEY:
        raise RuntimeError(
            "AZURE_SPEECH_KEY no configurada. "
            "Agrega la clave en el archivo .env."
            "Crea un recurso Speech en Azure Portal y agrega la clave al .env"
        )
    
    # Mapear content_type al formato que acepta Azure
    azure_content_type = CONTENT_TYPES_SOPORTADOS.get(
        content_type.split(";")[0].strip(),  # ignorar parámetros como "codecs=opus"
        "audio/wav",                          # fallback a WAV si no reconoce el tipo
    )



    region = settings.AZURE_SPEECH_REGION
    language = settings.AZURE_SPEECH_LANGUAGE

    url = (
        f"https://{region}.stt.speech.microsoft.com"
        "/speech/recognition/conversation/cognitiveservices/v1"
        f"?language={language}&format=simple"
    )

    headers = {
        "Ocp-Apim-Subscription-Key": settings.AZURE_SPEECH_KEY,
        "Content-Type": azure_content_type,
        "Accept": "application/json",
    }

    response = requests.post(url, headers=headers, data=audio_bytes, timeout=30)

    if response.status_code != 200:
        raise RuntimeError(
            f"Azure Speech devolvió {response.status_code}: {response.text}"
        )

    data = response.json()

    estado = data.get("RecognitionStatus", "")

    if estado == "Success":
        # "DisplayText" tiene el texto con puntuación y mayúsculas
        return data.get("DisplayText", "").strip()
    elif estado == "NoMatch":
        raise RuntimeError("No se reconoció voz en el audio. Verifica que el micrófono grabó correctamente.")
    elif estado == "InitialSilenceTimeout":
        raise RuntimeError("El audio está en silencio o es demasiado corto.")
    else:
        raise RuntimeError(
            f"Azure Speech: reconocimiento fallido — estado: {estado}"
        )

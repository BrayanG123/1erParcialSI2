import cloudinary
import cloudinary.uploader
from fastapi import UploadFile

from app.config import settings

# Configurar una sola vez al importar
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)

TIPOS_IMAGEN_PERMITIDOS = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = 5 * 1024 * 1024  # 5 MB

TIPOS_AUDIO_PERMITIDOS = {"audio/mpeg", "audio/mp4", "audio/aac", "audio/m4a", "audio/x-m4a"}
MAX_BYTES_AUDIO = 10 * 1024 * 1024  # 10 MB

def subir_imagen(archivo: UploadFile, carpeta: str) -> str:
    """
    Sube un archivo de imagen a Cloudinary y devuelve la URL segura (https).

    - carpeta: subcarpeta en Cloudinary (ej. 'incidentes', 'vehiculos')
    - Lanza ValueError si el tipo o tamaño no es válido.
    """
    if archivo.content_type not in TIPOS_IMAGEN_PERMITIDOS:
        raise ValueError(
            "Tipo de archivo no permitido. Usa JPG, PNG o WebP."
        )

    contenido = archivo.file.read()
    if len(contenido) > MAX_BYTES:
        raise ValueError("La imagen no puede superar 5 MB.")

    resultado = cloudinary.uploader.upload(
        contenido,
        folder=carpeta,
        resource_type="image",
        overwrite=True,
    )
    return resultado["secure_url"]


def subir_audio(archivo: UploadFile, carpeta: str) -> str:
    """
    Sube un archivo de audio a Cloudinary como recurso 'video' (Cloudinary
    trata audio y video bajo el mismo resource_type).
    Devuelve la URL segura.
    """
    # Cloudinary recibe audio como resource_type="video"
    contenido = archivo.file.read()
    if len(contenido) > MAX_BYTES_AUDIO:
        raise ValueError("El audio no puede superar 10 MB.")

    resultado = cloudinary.uploader.upload(
        contenido,
        folder=carpeta,
        resource_type="video",   # audio también usa "video" en Cloudinary
        overwrite=True,
    )
    return resultado["secure_url"]
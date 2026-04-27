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
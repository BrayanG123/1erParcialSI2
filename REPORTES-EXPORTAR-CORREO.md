# Reportes Dinámicos — Exportación (Excel/PDF) y Envío por Correo

**Fecha:** 2026-06-11
**Estado:** Implementado y verificado (generación de archivos probada con datos
reales). Pendiente de tu parte: configurar el SMTP con tu Gmail (sección 4).

Con esto el módulo de Reportes Dinámicos queda completo:
constructor manual + prompts por texto/voz con IA + exportación + envío por correo.

---

## 1. Qué se agregó

| Pieza | Archivo | Rol |
|-------|---------|-----|
| Generador de archivos | `backend/app/services/reporte_exportador.py` | Convierte el resultado de un QBE en bytes de `.xlsx` (openpyxl) o `.pdf` (fpdf2) |
| Servicio de correo | `backend/app/services/email_service.py` | Envía emails con adjuntos vía SMTP (librería estándar de Python, sin dependencias) |
| Endpoint de descarga | `POST /reportes/exportar?formato=excel\|pdf` | Ejecuta el QBE y devuelve el archivo descargable |
| Endpoint de envío | `POST /reportes/enviar-correo` | Genera el archivo y lo manda como adjunto al email indicado |
| Config | `app/config.py` + `.env` | Variables `SMTP_HOST/PORT/USER/PASSWORD/FROM` |
| UI | página `/admin/reportes` | Botones CSV / Excel / PDF / "✉ Enviar por correo" con panel inline |

Dependencias nuevas (ya instaladas y en `requirements.txt`): `openpyxl`, `fpdf2`.
Ambas son livianas y puras de Python — no afectan el Docker ni el despliegue.

---

## 2. Cómo funciona la exportación

### El flujo

```
[Constructor o IA]  →  QBE (JSON)  →  POST /reportes/exportar?formato=pdf
                                              │
                              ejecutar_qbe() con pagina=1, tamano_pagina=1000
                                              │
                              generar_excel() o generar_pdf()  →  bytes
                                              │
                              Response con Content-Disposition: attachment
                                              │
                       el navegador descarga "reporte_pagos_20260611_1530.pdf"
```

**Detalle importante:** la exportación ignora la paginación de la pantalla.
Aunque estés viendo la página 2 de 10, el archivo incluye **el reporte
completo hasta 1000 filas** (el tope del motor QBE). Esto es intencional:
nadie quiere un PDF con solo la página visible.

### Diferencia entre los tres botones

| Botón | Dónde se genera | Qué incluye |
|-------|------------------|-------------|
| ⬇ CSV | En el navegador (cliente) | Solo lo ya cargado en pantalla |
| ⬇ Excel | En el backend | Hasta 1000 filas, con formato (título, encabezado de color, columnas auto-ajustadas, panel congelado) |
| ⬇ PDF | En el backend | Hasta 1000 filas, A4 apaisado, tabla con cebra, encabezado repetido en cada página |

### Detalles técnicos que conviene conocer (por si algo falla)

- **Excel**: los números se escriben como números (puedes sumarlos en Excel);
  enums y fechas se normalizan a texto legible (`finalizado`, `11/06/2026 15:30`).
- **PDF**: las fuentes estándar de PDF solo soportan el alfabeto latin-1
  (incluye á é í ó ú ñ — suficiente para español). Un emoji u otro carácter
  exótico en los datos aparecería como `?` — es normal, no es un bug.
- **Frontend**: la descarga usa `responseType: 'blob'` y lee el nombre real
  del archivo del header `Content-Disposition`.

---

## 3. Cómo funciona el envío por correo

### El flujo completo

```
Usuario llena: destinatario + formato + mensaje opcional
        │
POST /reportes/enviar-correo  { qbe, destinatario, formato, mensaje }
        │
1. Valida el email (EmailStr de Pydantic — rechaza formatos inválidos)
2. Verifica que el SMTP esté configurado (si no → 503 con instrucciones)
3. Ejecuta el QBE (mismo motor, mismas whitelists, mismo aislamiento por tenant)
4. Genera el archivo (Excel o PDF)
5. Arma el correo:
     Asunto:  "Reporte Ejecutivo: pagos (245 registros)"
     Cuerpo:  resumen del reporte + mensaje del remitente si lo escribió
     Adjunto: reporte_pagos_20260611_1530.xlsx
6. Lo envía por SMTP con TLS (conexión cifrada)
        │
Respuesta: { enviado: true, destinatario, archivo, total_registros }
```

### El servicio de correo (`email_service.py`) por dentro

- Usa `smtplib` + `EmailMessage` de la **librería estándar** de Python:
  no hubo que instalar nada para esto.
- Soporta los dos modos de conexión segura:
  - **Puerto 587** (el por defecto): conexión normal que se "eleva" a cifrada
    con `STARTTLS` — es el modo estándar de Gmail.
  - **Puerto 465**: SSL directo desde el inicio (por si usas otro proveedor).
- Los errores se traducen a mensajes accionables: si Gmail rechaza las
  credenciales, el error te dice explícitamente que verifiques el App
  Password (el fallo más común).

---

## 4. CONFIGURACIÓN DEL SMTP — lo que te falta hacer (5 minutos)

El envío usa tu cuenta de Gmail como remitente. Gmail **no acepta tu
contraseña normal** desde aplicaciones: hay que generar un **App Password**
(contraseña de aplicación), que es una clave de 16 caracteres exclusiva
para esta app.

### Paso a paso

1. **Activa la verificación en 2 pasos** en tu cuenta Google (si no la tienes):
   https://myaccount.google.com/security → "Verificación en 2 pasos" → seguir el asistente.
   *(Sin esto, Google no te deja crear App Passwords.)*

2. **Crea el App Password**:
   - Ve a https://myaccount.google.com/apppasswords
   - Nombre de la app: `auxilio-vehicular` (o lo que quieras)
   - Google te muestra una clave de 16 caracteres tipo `abcd efgh ijkl mnop`
   - **Cópiala ya** — no se vuelve a mostrar.

3. **Configura el `.env`** del backend (las líneas ya están al final,
   solo descomenta y completa):

   ```env
   SMTP_USER=tucorreo@gmail.com
   SMTP_PASSWORD=abcd efgh ijkl mnop
   ```
   - Los espacios del App Password dan igual (Gmail los ignora).
   - `SMTP_HOST` y `SMTP_PORT` ya tienen los valores de Gmail por defecto
     (`smtp.gmail.com` / `587`) — no hace falta tocarlos.
   - `SMTP_FROM` es opcional (por defecto usa `SMTP_USER`).

4. **Reinicia el backend** y prueba desde la página de Reportes.

> 🔐 **Seguridad:** el App Password solo da acceso a enviar correo, puedes
> revocarlo cuando quieras desde la misma página de Google, y NUNCA va en
> el código ni en la imagen Docker — vive solo en el `.env` (local) o en
> las variables del App Service (Azure, agrégalas allá si despliegas).

### ¿Y si no quiero usar Gmail?

Cualquier SMTP sirve cambiando las variables. Ejemplos:
- **Outlook/Hotmail**: `SMTP_HOST=smtp-mail.outlook.com`, puerto 587
- **Brevo (ex Sendinblue)**: gratis 300 correos/día, `smtp-relay.brevo.com`,
  puerto 587 — buena opción si Gmail te da problemas en producción.

---

## 5. Cómo usarlo (manual de usuario)

1. Entra a **Reportes Dinámicos** (`/admin/reportes`).
2. Genera cualquier reporte: con el constructor manual, escribiendo un
   prompt o dictándolo por micrófono.
3. En la cabecera de los resultados:
   - **⬇ CSV / ⬇ Excel / ⬇ PDF** → descarga directa.
   - **✉ Enviar por correo** → abre el panel:
     - correo del destinatario (obligatorio, se valida)
     - formato del adjunto (Excel o PDF)
     - mensaje opcional (se incluye en el cuerpo del correo)
     - **Enviar** → confirma con "✓ Reporte enviado a ... (archivo, N registros)"
4. El destinatario recibe un correo con asunto descriptivo, el resumen del
   reporte en el cuerpo y el archivo adjunto.

> El envío usa **los criterios actuales del constructor** (lo que ves en los
> controles), no una "foto" del resultado en pantalla. Si cambiaste filtros
> después de generar, lo que se envía refleja los filtros nuevos.

---

## 6. Solución de problemas

| Síntoma | Causa | Solución |
|---------|-------|----------|
| 503 "El servidor de correo no está configurado" | Faltan `SMTP_USER`/`SMTP_PASSWORD` en el `.env` | Sección 4 (y reiniciar el backend) |
| 502 "Gmail rechazó las credenciales" | Pusiste tu contraseña normal, o sin verificación en 2 pasos | Genera el App Password (sección 4, paso 2) |
| 502 "No se pudo enviar el correo: timed out" | Red/firewall bloquea el puerto 587 | Prueba puerto 465 (`SMTP_PORT=465`), o desde otra red |
| El correo no llega | Suele estar en SPAM la primera vez | Revisar spam; marcar "no es spam" |
| 422 al enviar | Email del destinatario mal formado | Pydantic lo valida — corregir el email |
| El PDF muestra `?` en algunos textos | Carácter fuera de latin-1 (emoji, etc.) | Normal — limitación de las fuentes PDF estándar |
| El Excel/PDF solo trae 1000 filas | Tope del motor QBE | Es intencional; afina los filtros o el rango de fechas para reportes más específicos |
| En Azure no envía correos | Las variables SMTP no están en el App Service | Agregarlas con `az webapp config appsettings set` (igual que las demás) |

---

## 7. Mapa final del módulo de Reportes Dinámicos

```
                    ┌─────────────────────────────────────────┐
  Texto escrito ───►│                                         │
                    │  POST /reportes/desde-texto             │
  Voz (micrófono) ─►│   └─ Azure STT → texto                  │──┐
                    │   └─ Groq (Llama 3.3) → QBE JSON        │  │
                    └─────────────────────────────────────────┘  │
                                                                 ▼
  Constructor ────► QBE (JSON) ────► MOTOR QBE (whitelists + tenant)
  manual                                      │
                                              ▼
                              ┌───────────────┴───────────────┐
                              ▼               ▼               ▼
                        Tabla en línea   /exportar       /enviar-correo
                        (paginada)       Excel | PDF     SMTP + adjunto
```

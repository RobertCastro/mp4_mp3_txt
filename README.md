# Conversión de Videos a MP3 y Transcripción a Texto

Este proyecto contiene dos scripts que trabajan en secuencia:

1. **video_to_mp3.py**: Convierte todos los videos de la carpeta `videos/` a archivos MP3 y los guarda en `mp3/`
2. **mp3_to_txt.py**: Transcribe todos los archivos MP3 de la carpeta `mp3/` a archivos de texto y los guarda en `txt/`

## Requisitos del Sistema

### Dependencias del Sistema

- **Python 3.7+**
- **ffmpeg**: Necesario para la conversión de video a audio
  - Ubuntu/Debian: `sudo apt install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Windows: Descargar desde [ffmpeg.org](https://ffmpeg.org/download.html)

### Dependencias de Python

Las dependencias se instalan automáticamente con el comando de instalación (ver abajo).

## Instalación

### 1. Crear un entorno virtual (recomendado)

```bash
# Desde la carpeta mp4_mp3_txt
python3 -m venv venv

# Activar el entorno virtual
# En Linux/macOS:
source venv/bin/activate
# En Windows:
venv\Scripts\activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

Esto instalará:
- `ffmpeg-python`: Para la conversión de video a audio
- `openai-whisper`: Para la transcripción de audio a texto

**Nota**: La primera vez que ejecutes el script de transcripción, Whisper descargará automáticamente el modelo de lenguaje:
- Modelo `tiny`: ~75 MB
- Modelo `base`: ~150 MB
- Modelo `small`: ~500 MB

## Uso

### Ejecución Automática (Recomendado)

El primer script ejecutará automáticamente el segundo al terminar:

```bash
python video_to_mp3.py
```

Este comando:
1. Convertirá todos los videos de `videos/` a MP3 en `mp3/`
2. Al terminar, ejecutará automáticamente `mp3_to_txt.py`
3. Transcribirá todos los MP3 a archivos de texto en `txt/`

### Ejecución Manual

Si prefieres ejecutar los scripts por separado:

```bash
# Solo convertir videos a MP3
python video_to_mp3.py

# Solo transcribir MP3 a texto
python mp3_to_txt.py
```

## Estructura de Carpetas

```
mp4_mp3_txt/
├── videos/          # Coloca aquí tus archivos de video
├── mp3/             # Se generan aquí los archivos MP3
├── txt/             # Se generan aquí los archivos de texto
├── video_to_mp3.py  # Script de conversión video -> MP3
├── mp3_to_txt.py    # Script de transcripción MP3 -> TXT
├── requirements.txt # Dependencias de Python
└── README.md        # Este archivo
```

## Formatos Soportados

### Videos (entrada)
- MP4, AVI, MOV, MKV, FLV, WMV, WEBM, M4V

### Audio (intermedio)
- MP3

### Texto (salida)
- TXT (UTF-8)

## Notas Importantes

1. **División automática de archivos grandes**: Si un archivo MP3 es mayor a 50 MB (configurable), se dividirá automáticamente en chunks más pequeños de 30 minutos cada uno. Los chunks se nombran como `original_part1.mp3`, `original_part2.mp3`, etc. Después de transcribir, los archivos de texto se unen automáticamente en un solo archivo `original.txt`.
   
   **Configuración**:
   ```bash
   # Cambiar tamaño máximo antes de dividir (por defecto: 50 MB)
   export MP3_MAX_SIZE_MB=60
   
   # Cambiar duración de cada chunk en minutos (por defecto: 30)
   export MP3_CHUNK_MINUTES=20
   ```

2. **Nombres de archivos**: Los archivos de salida mantendrán el mismo nombre que los archivos de entrada, solo cambiará la extensión.

3. **Modelo de Whisper**: El script usa el modelo `tiny` por defecto para reducir el uso de memoria (~1GB). Si tienes más memoria disponible y quieres mejor calidad, puedes cambiar el modelo usando una variable de entorno:
   ```bash
   # Para usar el modelo 'base' (mejor calidad, similar memoria)
   export WHISPER_MODEL=base
   python mp3_to_txt.py
   
   # Para usar el modelo 'small' (muy buena calidad, requiere ~2GB)
   export WHISPER_MODEL=small
   python mp3_to_txt.py
   ```
   
   Modelos disponibles:
   - `tiny`: ~1GB RAM, más rápido, menor precisión
   - `base`: ~1GB RAM, balance velocidad/precisión (recomendado si tienes memoria)
   - `small`: ~2GB RAM, buena precisión
   - `medium`: ~5GB RAM, muy buena precisión
   - `large`: ~10GB RAM, mejor precisión

4. **Archivos existentes**: Si un archivo de texto ya existe, el script de transcripción lo saltará automáticamente.

5. **Idioma**: Por defecto, el script fuerza el idioma a español (`es`). Puedes cambiar esto con una variable de entorno:
   ```bash
   # Forzar español (por defecto)
   export WHISPER_LANGUAGE=es
   python mp3_to_txt.py
   
   # Forzar inglés
   export WHISPER_LANGUAGE=en
   python mp3_to_txt.py
   
   # Detección automática (si prefieres que Whisper detecte el idioma)
   export WHISPER_LANGUAGE=auto
   python mp3_to_txt.py
   ```
   
   Códigos de idioma comunes: `es` (español), `en` (inglés), `fr` (francés), `de` (alemán), `it` (italiano), `pt` (portugués), etc.

6. **Optimización de memoria**: El script está ULTRA-optimizado para usar la mínima memoria posible:
   - **Modo por defecto**: Carga y descarga el modelo para cada archivo (más lento pero usa MUCHO menos memoria)
   - Usa CPU por defecto (evita problemas de VRAM)
   - Desactiva gradientes de PyTorch
   - Usa `torch.inference_mode()` para reducir memoria
   - Usa beam_size=1 (greedy decoding) para mínimo uso de memoria
   - Usa best_of=1 para evitar múltiples intentos
   - Limpia memoria agresivamente después de cada transcripción
   
   **Para desactivar el modo ultra-optimizado** (más rápido pero usa más memoria):
   ```bash
   export WHISPER_LOAD_PER_FILE=false
   python mp3_to_txt.py
   ```

## Solución de Problemas

### Error: "ffmpeg no encontrado"
- Instala ffmpeg en tu sistema (ver sección de Requisitos del Sistema)

### Error: "No se encontraron videos"
- Asegúrate de que los archivos de video estén en la carpeta `videos/`
- Verifica que las extensiones de los archivos sean compatibles

### Error: "Modelo de Whisper no se descarga"
- Verifica tu conexión a internet (la primera ejecución requiere descargar el modelo)
- Si tienes problemas, puedes descargar manualmente el modelo desde [GitHub](https://github.com/openai/whisper)

### Error: "Killed" o proceso terminado
- Esto indica que el proceso se quedó sin memoria (OOM)
- **Soluciones implementadas**:
  1. El script usa el modelo `tiny` por defecto
  2. Carga y descarga el modelo para cada archivo (modo ultra-optimizado activado por defecto)
  3. Usa parámetros que minimizan el uso de memoria
  4. Divide automáticamente archivos MP3 mayores a 50 MB en chunks más pequeños
  5. Une automáticamente los archivos de texto resultantes
- **Si aún tienes problemas**:
  - Asegúrate de tener al menos 1.5GB de RAM libre
  - Cierra otras aplicaciones que usen mucha memoria
  - Verifica que el modo ultra-optimizado esté activado: `export WHISPER_LOAD_PER_FILE=true`
  - Reduce el tamaño máximo antes de dividir: `export MP3_MAX_SIZE_MB=40`
  - Reduce la duración de los chunks: `export MP3_CHUNK_MINUTES=20`
  - Si tienes muy poca RAM, considera usar un servicio de transcripción en la nube

### Rendimiento lento
- El modelo `tiny` es el más rápido pero menos preciso
- Para mejor calidad sin mucho impacto en memoria, usa `base`: `export WHISPER_MODEL=base`
- Para mayor precisión, usa `small`, `medium` o `large` (requiere más memoria y es más lento)

## Ejemplo de Uso

```bash
# 1. Coloca tus videos en videos/
cp mi_video.mp4 mp4_mp3_txt/videos/

# 2. Ejecuta el script principal
cd mp4_mp3_txt
python video_to_mp3.py

# 3. Resultados:
# - videos/mi_video.mp4 -> mp3/mi_video.mp3
# - mp3/mi_video.mp3 -> txt/mi_video.txt
```

## Licencia

Este proyecto utiliza:
- **ffmpeg-python**: Licencia MIT
- **openai-whisper**: Licencia MIT


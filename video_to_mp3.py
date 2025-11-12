#!/usr/bin/env python3
"""
Script para convertir videos de la carpeta videos/ a archivos MP3
y guardarlos en la carpeta mp3/ con el mismo nombre.
Si los archivos son muy grandes, los divide en chunks más pequeños.
"""
import os
import sys
from pathlib import Path
import ffmpeg
import math


def extraer_audio(video_path, audio_path):
    """
    Extrae el audio de un video y lo guarda como MP3.
    
    Args:
        video_path: Ruta al archivo de video
        audio_path: Ruta donde se guardará el archivo MP3
    """
    try:
        (
            ffmpeg
            .input(video_path)
            .output(audio_path, format='mp3', acodec='libmp3lame')
            .run(quiet=True, overwrite_output=True)
        )
        return True
    except Exception as e:
        print(f"Error al convertir {video_path}: {e}")
        return False


def obtener_duracion_audio(audio_path):
    """
    Obtiene la duración de un archivo de audio en segundos.
    
    Args:
        audio_path: Ruta al archivo de audio
        
    Returns:
        Duración en segundos, o None si hay error
    """
    try:
        probe = ffmpeg.probe(str(audio_path))
        duration = float(probe['streams'][0].get('duration', 0))
        return duration
    except Exception as e:
        print(f"   Error al obtener duración: {e}")
        return None


def dividir_audio(audio_path, output_dir, max_size_mb=50, chunk_duration_minutes=30):
    """
    Divide un archivo de audio grande en chunks más pequeños.
    
    Args:
        audio_path: Ruta al archivo de audio a dividir
        output_dir: Directorio donde guardar los chunks
        max_size_mb: Tamaño máximo en MB (si el archivo es mayor, se divide)
        chunk_duration_minutes: Duración de cada chunk en minutos
        
    Returns:
        Lista de rutas a los chunks creados, o None si no se dividió
    """
    # Verificar tamaño del archivo
    file_size_mb = audio_path.stat().st_size / (1024 * 1024)
    
    if file_size_mb <= max_size_mb:
        return None  # No necesita dividirse
    
    print(f"   Archivo grande detectado ({file_size_mb:.1f} MB). Dividiendo en chunks...")
    
    # Obtener duración
    duration = obtener_duracion_audio(audio_path)
    if duration is None:
        return None
    
    # Calcular número de chunks necesarios
    chunk_duration_seconds = chunk_duration_minutes * 60
    num_chunks = math.ceil(duration / chunk_duration_seconds)
    
    print(f"   Duración: {duration/60:.1f} minutos. Creando {num_chunks} chunk(s)...")
    
    # Crear chunks
    chunks = []
    base_name = audio_path.stem
    
    for i in range(num_chunks):
        start_time = i * chunk_duration_seconds
        chunk_path = output_dir / f"{base_name}_part{i+1}.mp3"
        
        # Calcular duración real del chunk (el último puede ser más corto)
        remaining_duration = duration - start_time
        actual_chunk_duration = min(chunk_duration_seconds, remaining_duration)
        
        if actual_chunk_duration <= 0:
            break  # No hay más audio que procesar
        
        try:
            (
                ffmpeg
                .input(str(audio_path), ss=start_time, t=actual_chunk_duration)
                .output(str(chunk_path), format='mp3', acodec='libmp3lame')
                .run(quiet=True, overwrite_output=True)
            )
            chunks.append(chunk_path)
            print(f"   Creado: {chunk_path.name} ({actual_chunk_duration/60:.1f} min)")
        except Exception as e:
            print(f"   Error al crear chunk {i+1}: {e}")
            # Limpiar chunks creados en caso de error
            for chunk in chunks:
                if chunk.exists():
                    chunk.unlink()
            return None
    
    # Eliminar el archivo original grande
    try:
        audio_path.unlink()
        print(f"   Archivo original eliminado (dividido en {len(chunks)} partes)")
    except Exception as e:
        print(f"   Advertencia: No se pudo eliminar el archivo original: {e}")
    
    return chunks


def convertir_videos_a_mp3():
    """
    Convierte todos los videos de la carpeta videos/ a MP3
    y los guarda en la carpeta mp3/.
    """
    # Obtener la ruta del directorio del script
    script_dir = Path(__file__).parent
    videos_dir = script_dir / "videos"
    mp3_dir = script_dir / "mp3"
    
    # Crear carpeta mp3 si no existe
    mp3_dir.mkdir(parents=True, exist_ok=True)
    
    # Verificar que existe la carpeta videos
    if not videos_dir.exists():
        print(f"La carpeta {videos_dir} no existe.")
        return False
    
    # Extensiones de video comunes
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v'}
    
    # Buscar todos los archivos de video
    video_files = [f for f in videos_dir.iterdir() 
                   if f.is_file() and f.suffix.lower() in video_extensions]
    
    if not video_files:
        print(f"No se encontraron videos en {videos_dir}")
        return False
    
    print(f"Encontrados {len(video_files)} video(s) para convertir...")
    
    # Tamaño máximo en MB antes de dividir (configurable con variable de entorno)
    max_size_mb = int(os.getenv("MP3_MAX_SIZE_MB", "50"))
    chunk_duration_minutes = int(os.getenv("MP3_CHUNK_MINUTES", "30"))
    
    # Convertir cada video
    success_count = 0
    for video_file in video_files:
        # Crear nombre del archivo MP3 (mismo nombre, extensión .mp3)
        mp3_filename = video_file.stem + ".mp3"
        mp3_path = mp3_dir / mp3_filename
        
        print(f"Convirtiendo: {video_file.name} -> {mp3_filename}")
        
        if extraer_audio(str(video_file), str(mp3_path)):
            print(f"Convertido exitosamente: {mp3_filename}")
            
            # Verificar si necesita dividirse
            chunks = dividir_audio(mp3_path, mp3_dir, max_size_mb, chunk_duration_minutes)
            if chunks:
                print(f"   Dividido en {len(chunks)} parte(s)")
            
            success_count += 1
        else:
            print(f"Falló la conversión de: {video_file.name}")
    
    print(f"\nResumen: {success_count}/{len(video_files)} videos convertidos exitosamente.")
    return success_count == len(video_files)


if __name__ == "__main__":
    print("=" * 60)
    print("CONVERSOR DE VIDEOS A MP3")
    print("=" * 60)
    
    success = convertir_videos_a_mp3()
    
    if success:
        print("\n Proceso completado. Iniciando transcripción...")
        # Ejecutar el segundo script
        script_dir = Path(__file__).parent
        mp3_to_txt_script = script_dir / "mp3_to_txt.py"
        
        if mp3_to_txt_script.exists():
            print("\n" + "=" * 60)
            print("INICIANDO TRANSCRIPCIÓN DE AUDIO A TEXTO")
            print("=" * 60)
            os.system(f"{sys.executable} {mp3_to_txt_script}")
        else:
            print(f"No se encontró el script {mp3_to_txt_script}")
    else:
        print("\n Algunas conversiones fallaron. Revisa los errores arriba.")
        sys.exit(1)


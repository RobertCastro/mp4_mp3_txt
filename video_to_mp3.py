#!/usr/bin/env python3
"""
Script para convertir videos de la carpeta videos/ a archivos MP3
y guardarlos en la carpeta mp3/ con el mismo nombre.
"""
import os
import sys
from pathlib import Path
import ffmpeg


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
        print(f"❌ Error al convertir {video_path}: {e}")
        return False


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
        print(f"❌ La carpeta {videos_dir} no existe.")
        return False
    
    # Extensiones de video comunes
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v'}
    
    # Buscar todos los archivos de video
    video_files = [f for f in videos_dir.iterdir() 
                   if f.is_file() and f.suffix.lower() in video_extensions]
    
    if not video_files:
        print(f"⚠️  No se encontraron videos en {videos_dir}")
        return False
    
    print(f"📹 Encontrados {len(video_files)} video(s) para convertir...")
    
    # Convertir cada video
    success_count = 0
    for video_file in video_files:
        # Crear nombre del archivo MP3 (mismo nombre, extensión .mp3)
        mp3_filename = video_file.stem + ".mp3"
        mp3_path = mp3_dir / mp3_filename
        
        print(f"🔄 Convirtiendo: {video_file.name} -> {mp3_filename}")
        
        if extraer_audio(str(video_file), str(mp3_path)):
            print(f"✅ Convertido exitosamente: {mp3_filename}")
            success_count += 1
        else:
            print(f"❌ Falló la conversión de: {video_file.name}")
    
    print(f"\n📊 Resumen: {success_count}/{len(video_files)} videos convertidos exitosamente.")
    return success_count == len(video_files)


if __name__ == "__main__":
    print("=" * 60)
    print("🎬 CONVERSOR DE VIDEOS A MP3")
    print("=" * 60)
    
    success = convertir_videos_a_mp3()
    
    if success:
        print("\n✅ Proceso completado. Iniciando transcripción...")
        # Ejecutar el segundo script
        script_dir = Path(__file__).parent
        mp3_to_txt_script = script_dir / "mp3_to_txt.py"
        
        if mp3_to_txt_script.exists():
            print("\n" + "=" * 60)
            print("🎤 INICIANDO TRANSCRIPCIÓN DE AUDIO A TEXTO")
            print("=" * 60)
            os.system(f"{sys.executable} {mp3_to_txt_script}")
        else:
            print(f"⚠️  No se encontró el script {mp3_to_txt_script}")
    else:
        print("\n⚠️  Algunas conversiones fallaron. Revisa los errores arriba.")
        sys.exit(1)


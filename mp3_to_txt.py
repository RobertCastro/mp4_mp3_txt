#!/usr/bin/env python3
"""
Script para transcribir archivos MP3 de la carpeta mp3/ a archivos de texto
y guardarlos en la carpeta txt/ con el mismo nombre.
"""
import os
import gc
from pathlib import Path
import whisper
import torch


def transcribir_audio(mp3_path, txt_path, model):
    """
    Transcribe un archivo de audio MP3 a texto.
    Optimizado para usar menos memoria.
    
    Args:
        mp3_path: Ruta al archivo MP3
        txt_path: Ruta donde se guardará el archivo de texto
        model: Modelo de Whisper ya cargado
    """
    try:
        print(f"   🎤 Transcribiendo audio...")
        # Transcribir el audio con parámetros optimizados para memoria
        # fp16=False: usar float32 en CPU para evitar problemas de memoria
        # condition_on_previous_text=False: reduce uso de memoria
        result = model.transcribe(
            str(mp3_path),
            fp16=False,  # No usar FP16 en CPU
            condition_on_previous_text=False,  # Reduce memoria
            verbose=False  # Menos output
        )
        
        # Obtener el texto transcrito
        texto = result["text"]
        
        # Guardar el texto en el archivo
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(texto)
        
        # Limpiar memoria
        del result
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        return True
    except Exception as e:
        print(f"   ❌ Error al transcribir {mp3_path}: {e}")
        # Limpiar memoria incluso en caso de error
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return False


def transcribir_mp3s_a_txt():
    """
    Transcribe todos los archivos MP3 de la carpeta mp3/ a archivos de texto
    y los guarda en la carpeta txt/.
    """
    # Obtener la ruta del directorio del script
    script_dir = Path(__file__).parent
    mp3_dir = script_dir / "mp3"
    txt_dir = script_dir / "txt"
    
    # Crear carpeta txt si no existe
    txt_dir.mkdir(parents=True, exist_ok=True)
    
    # Verificar que existe la carpeta mp3
    if not mp3_dir.exists():
        print(f"❌ La carpeta {mp3_dir} no existe.")
        return False
    
    # Buscar todos los archivos MP3
    mp3_files = [f for f in mp3_dir.iterdir() 
                 if f.is_file() and f.suffix.lower() == '.mp3']
    
    if not mp3_files:
        print(f"⚠️  No se encontraron archivos MP3 en {mp3_dir}")
        return False
    
    print(f"🎵 Encontrados {len(mp3_files)} archivo(s) MP3 para transcribir...")
    
    # Cargar el modelo de Whisper una sola vez (se descarga automáticamente la primera vez)
    # Usamos 'tiny' para reducir uso de memoria (requiere ~1GB)
    # Si tienes más memoria, puedes cambiar a 'base' o 'small'
    # Opciones: 'tiny' (~1GB), 'base' (~1GB), 'small' (~2GB), 'medium' (~5GB), 'large' (~10GB)
    model_name = os.getenv("WHISPER_MODEL", "tiny")  # Permite cambiar con variable de entorno
    
    print(f"📥 Cargando modelo Whisper '{model_name}' (esto puede tardar la primera vez)...")
    print("   💡 Tip: Si tienes problemas de memoria, usa 'tiny'. Para mejor calidad, usa 'base' o 'small'")
    
    try:
        # Forzar CPU si no hay GPU o si hay problemas de memoria
        device = "cpu"  # Usar CPU para evitar problemas de VRAM
        model = whisper.load_model(model_name, device=device)
        print(f"✅ Modelo '{model_name}' cargado exitosamente en {device}.\n")
    except Exception as e:
        print(f"❌ Error al cargar el modelo de Whisper: {e}")
        return False
    
    # Transcribir cada MP3
    success_count = 0
    for i, mp3_file in enumerate(mp3_files, 1):
        # Crear nombre del archivo TXT (mismo nombre, extensión .txt)
        txt_filename = mp3_file.stem + ".txt"
        txt_path = txt_dir / txt_filename
        
        # Verificar si ya existe el archivo de texto
        if txt_path.exists():
            print(f"[{i}/{len(mp3_files)}] ⏭️  Saltando {mp3_file.name} (ya existe {txt_filename})")
            success_count += 1
            continue
        
        print(f"[{i}/{len(mp3_files)}] 🔄 Transcribiendo: {mp3_file.name} -> {txt_filename}")
        
        if transcribir_audio(mp3_file, txt_path, model):
            print(f"   ✅ Transcrito exitosamente: {txt_filename}")
            success_count += 1
        else:
            print(f"   ❌ Falló la transcripción de: {mp3_file.name}")
        
        # Limpiar memoria después de cada archivo
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    print(f"\n📊 Resumen: {success_count}/{len(mp3_files)} archivos transcritos exitosamente.")
    
    # Limpiar memoria final
    del model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    return success_count == len(mp3_files)


if __name__ == "__main__":
    print("=" * 60)
    print("🎤 TRANSCRIPCIÓN DE AUDIO A TEXTO")
    print("=" * 60)
    
    success = transcribir_mp3s_a_txt()
    
    if success:
        print("\n✅ Proceso de transcripción completado.")
    else:
        print("\n⚠️  Algunas transcripciones fallaron. Revisa los errores arriba.")
        exit(1)


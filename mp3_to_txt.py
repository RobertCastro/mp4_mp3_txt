#!/usr/bin/env python3
"""
Script para transcribir archivos MP3 de la carpeta mp3/ a archivos de texto
y guardarlos en la carpeta txt/ con el mismo nombre.
Optimizado para usar la mínima memoria posible.
"""
import os
import gc
import re
from pathlib import Path
from collections import defaultdict
import whisper
import torch

# Desactivar gradientes para reducir memoria
torch.set_grad_enabled(False)


def transcribir_audio(mp3_path, txt_path, model, language=None):
    """
    Transcribe un archivo de audio MP3 a texto.
    Altamente optimizado para usar la mínima memoria posible.
    
    Args:
        mp3_path: Ruta al archivo MP3
        txt_path: Ruta donde se guardará el archivo de texto
        model: Modelo de Whisper ya cargado
        language: Código de idioma (ej: 'es' para español, 'en' para inglés). 
                  Si es None, Whisper detectará el idioma automáticamente.
    """
    try:
        if language:
            print(f"   🎤 Transcribiendo audio (idioma forzado: {language})...")
        else:
            print(f"   🎤 Transcribiendo audio (detectando idioma)...")
        
        # Usar inference_mode para reducir memoria
        with torch.inference_mode():
            # Parámetros base
            transcribe_params = {
                'fp16': False,  # No usar FP16 en CPU
                'condition_on_previous_text': False,  # Reduce memoria significativamente
                'verbose': False,  # Menos output
                # Parámetros de decodificación para reducir memoria
                'beam_size': 1,  # Beam search mínimo (greedy decoding) - reduce memoria
                'best_of': 1,  # No hacer múltiples intentos - reduce memoria
                'temperature': 0,  # Determinístico, menos memoria
                # Umbrales de detección
                'compression_ratio_threshold': 2.4,
                'logprob_threshold': -1.0,
                'no_speech_threshold': 0.6,
            }
            
            # Agregar idioma si se especificó
            if language:
                transcribe_params['language'] = language
            
            # Transcribir el audio con parámetros ultra-optimizados para memoria
            result = model.transcribe(str(mp3_path), **transcribe_params)
        
        # Obtener el texto transcrito inmediatamente
        texto = result["text"]
        
        # Guardar el texto en el archivo
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(texto)
        
        # Limpiar memoria agresivamente
        del result
        del texto
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        return True
    except Exception as e:
        print(f"   Error al transcribir {mp3_path}: {e}")
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
        print(f"La carpeta {mp3_dir} no existe.")
        return False
    
    # Buscar todos los archivos MP3
    mp3_files = [f for f in mp3_dir.iterdir() 
                 if f.is_file() and f.suffix.lower() == '.mp3']
    
    if not mp3_files:
        print(f"No se encontraron archivos MP3 en {mp3_dir}")
        return False
    
    print(f"🎵 Encontrados {len(mp3_files)} archivo(s) MP3 para transcribir...")
    
    # Usamos 'tiny' para reducir uso de memoria al máximo
    # Opciones: 'tiny' (~1GB), 'base' (~1GB), 'small' (~2GB), 'medium' (~5GB), 'large' (~10GB)
    model_name = os.getenv("WHISPER_MODEL", "tiny")  # Permite cambiar con variable de entorno
    
    # Idioma para transcripción (None = detección automática, 'es' = español, 'en' = inglés, etc.)
    # Por defecto: español ('es')
    language = os.getenv("WHISPER_LANGUAGE", "es")
    if language.lower() == "none" or language.lower() == "auto":
        language = None
        print("   Idioma: Detección automática")
    else:
        print(f"   Idioma: {language} (forzado)")
    
    # ESTRATEGIA: Cargar y descargar el modelo para cada archivo
    # Esto es más lento pero usa MUCHO menos memoria acumulada
    load_model_per_file = os.getenv("WHISPER_LOAD_PER_FILE", "true").lower() == "true"
    
    if load_model_per_file:
        print("Modo ultra-optimizado: cargando modelo por archivo (usa menos memoria)")
        print(f"   Modelo: '{model_name}'")
        print("   Esto será más lento pero evitará problemas de memoria\n")
        model = None  # No cargar modelo globalmente
    else:
        print(f"Cargando modelo Whisper '{model_name}' (esto puede tardar la primera vez)...")
        print("   Tip: Si tienes problemas de memoria, usa WHISPER_LOAD_PER_FILE=true")
        
        try:
            device = "cpu"  # Usar CPU para evitar problemas de VRAM
            model = whisper.load_model(model_name, device=device)
            print(f"Modelo '{model_name}' cargado exitosamente en {device}.\n")
        except Exception as e:
            print(f"Error al cargar el modelo de Whisper: {e}")
            return False
    
    # Transcribir cada MP3
    success_count = 0
    for i, mp3_file in enumerate(mp3_files, 1):
        # Crear nombre del archivo TXT (mismo nombre, extensión .txt)
        txt_filename = mp3_file.stem + ".txt"
        txt_path = txt_dir / txt_filename
        
        # Verificar si ya existe el archivo de texto
        if txt_path.exists():
            print(f"[{i}/{len(mp3_files)}] ⏭Saltando {mp3_file.name} (ya existe {txt_filename})")
            success_count += 1
            continue
        
        print(f"[{i}/{len(mp3_files)}] Transcribiendo: {mp3_file.name} -> {txt_filename}")
        
        # Cargar modelo si estamos en modo per-file
        if load_model_per_file:
            try:
                print(f"   Cargando modelo '{model_name}'...")
                device = "cpu"
                model = whisper.load_model(model_name, device=device)
            except Exception as e:
                print(f"   Error al cargar el modelo: {e}")
                continue
        
        # Transcribir
        if transcribir_audio(mp3_file, txt_path, model, language=language):
            print(f"   Transcrito exitosamente: {txt_filename}")
            success_count += 1
        else:
            print(f"   Falló la transcripción de: {mp3_file.name}")
        
        # Si estamos en modo per-file, descargar el modelo después de cada archivo
        if load_model_per_file and model is not None:
            print(f"   Liberando modelo de memoria...")
            del model
            model = None
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        
        # Limpiar memoria después de cada archivo
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    print(f"\n Resumen: {success_count}/{len(mp3_files)} archivos transcritos exitosamente.")
    
    # Limpiar memoria final
    if model is not None:
        del model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    # Unir archivos TXT relacionados (partes de archivos divididos)
    unir_archivos_relacionados(txt_dir)
    
    return success_count == len(mp3_files)


def unir_archivos_relacionados(txt_dir):
    """
    Detecta archivos TXT que son partes de un mismo archivo original
    (terminan en _partN.txt) y los une en un solo archivo.
    
    Args:
        txt_dir: Directorio donde están los archivos TXT
    """
    # Buscar archivos que terminan en _partN.txt
    pattern = re.compile(r'^(.+)_part(\d+)\.txt$')
    
    # Agrupar archivos relacionados
    grupos = defaultdict(list)
    for txt_file in txt_dir.iterdir():
        if txt_file.is_file() and txt_file.suffix == '.txt':
            match = pattern.match(txt_file.name)
            if match:
                base_name = match.group(1)
                part_num = int(match.group(2))
                grupos[base_name].append((part_num, txt_file))
    
    if not grupos:
        return  # No hay archivos para unir
    
    print(f"\n Uniendo {len(grupos)} archivo(s) dividido(s)...")
    
    for base_name, partes in grupos.items():
        # Ordenar por número de parte
        partes.sort(key=lambda x: x[0])
        
        # Crear archivo unificado
        archivo_unificado = txt_dir / f"{base_name}.txt"
        
        print(f"   Uniendo {len(partes)} parte(s) -> {archivo_unificado.name}")
        
        try:
            with open(archivo_unificado, 'w', encoding='utf-8') as f_out:
                for i, (part_num, txt_file) in enumerate(partes):
                    with open(txt_file, 'r', encoding='utf-8') as f_in:
                        contenido = f_in.read().strip()
                        if contenido:
                            f_out.write(contenido)
                            # Agregar separador entre partes (excepto al final)
                            if i < len(partes) - 1:
                                f_out.write("\n\n")
            
            # Eliminar archivos parciales
            for _, txt_file in partes:
                try:
                    txt_file.unlink()
                    print(f"     Eliminado: {txt_file.name}")
                except Exception as e:
                    print(f"     Advertencia: No se pudo eliminar {txt_file.name}: {e}")
            
            print(f"   Archivo unificado creado: {archivo_unificado.name}")
            
        except Exception as e:
            print(f"   Error al unir archivos para {base_name}: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("TRANSCRIPCIÓN DE AUDIO A TEXTO")
    print("=" * 60)
    
    success = transcribir_mp3s_a_txt()
    
    if success:
        print("\n Proceso de transcripción completado.")
    else:
        print("\n Algunas transcripciones fallaron. Revisa los errores arriba.")
        exit(1)


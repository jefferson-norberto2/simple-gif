---
name: video-gif-core
description: >-
  Use this skill when implementing, refactoring, or optimizing video-to-GIF conversion routines,
  handling video capture with OpenCV, streaming frames to ImageIO, calculating dynamic FPS/durations,
  or applying adaptive palette quantization in the simple-gif project.
---

# Video to GIF Core Development Skill

Este guia orienta a implementação e manutenção do motor de conversão de vídeo para GIF no projeto **simple-gif**.

## 1. Diretrizes de Arquitetura do Motor

O motor em [`simplegif/simplegif.py`](file:///C:/Users/jmn/Documents/dev/python/simple-gif/simplegif/simplegif.py) deve ser puramente computacional, independente de UI e focado em eficiência.

### Pipeline de Conversão Recomendado (Streaming)
Em vez de carregar milhares de frames na memória, use o padrão de streaming:

```python
import cv2
import imageio
from pathlib import Path
from typing import Callable

def convert_video_stream(
    input_path: Path,
    output_path: Path,
    scale: float = 0.6,
    frame_skip: int = 5,
    max_frames: int = 2000,
    progress_callback: Callable[[int, int], None] | None = None
) -> Path:
    input_path = Path(input_path).resolve()
    output_path = Path(output_path).resolve()
    
    if not input_path.is_file():
        raise FileNotFoundError(f"Arquivo de vídeo não encontrado: {input_path}")
        
    output_dir = output_path.parent if output_path.suffix == ".gif" else output_path
    output_dir.mkdir(parents=True, exist_ok=True)
    
    dest_file = output_path if output_path.suffix == ".gif" else output_dir / f"{input_path.stem}.gif"
    
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise RuntimeError(f"Falha ao abrir vídeo: {input_path}")
        
    try:
        orig_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        target_frames = min(total_frames, max_frames) if total_frames > 0 else max_frames
        target_w = max(1, int(orig_w * scale))
        target_h = max(1, int(orig_h * scale))
        
        # Duração precisa entre frames capturados (em segundos para imageio ou ms para Pillow)
        effective_fps = max(1.0, orig_fps / frame_skip)
        duration_per_frame = 1.0 / effective_fps
        
        frame_idx = 0
        written_frames = 0
        
        with imageio.get_writer(dest_file, mode='I', duration=duration_per_frame, loop=0) as writer:
            while frame_idx < target_frames:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break
                    
                if frame_idx % frame_skip == 0:
                    resized = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_AREA)
                    rgb_frame = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                    writer.append_data(rgb_frame)
                    written_frames += 1
                    
                frame_idx += 1
                if progress_callback:
                    progress_callback(frame_idx, target_frames)
                    
        return dest_file
    finally:
        cap.release()
```

## 2. Checklist para Alterações no Core
- [ ] O caminho do arquivo foi tratado com `pathlib.Path`?
- [ ] O arquivo de vídeo foi verificado com `cap.isOpened()`?
- [ ] Os recursos do OpenCV (`cap.release()`) e do ImageIO (`writer.close()`) são liberados mesmo em caso de erro?
- [ ] A duração do frame no GIF reflete o FPS real do vídeo e o `frame_skip` escolhido?
- [ ] A escrita em disco e o processamento evitam alocar listas gigantes de imagens na memória RAM?

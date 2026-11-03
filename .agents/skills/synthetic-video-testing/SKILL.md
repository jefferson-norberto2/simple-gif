---
name: synthetic-video-testing
description: >-
  Use this skill when writing, generating, or running automated unit and integration tests with pytest
  for the simple-gif project using synthetic OpenCV test videos.
---

# Synthetic Video Testing Skill

Este guia orienta como criar fixtures de vídeo sintético e rodar testes automatizados sem depender de vídeos reais ou downloads externos.

## 1. Padrão de Fixture de Vídeo Sintético (`conftest.py`)

Para manter os testes rápidos, determinísticos e 100% offline, utilize o OpenCV para gerar arquivos `.mp4` pequenos sob demanda em pastas temporárias:

```python
import pytest
import cv2
import numpy as np
from pathlib import Path

@pytest.fixture
def sample_video_path(tmp_path: Path) -> Path:
    """Gera um vídeo sintético MP4 de 15 quadros a 30 FPS para testes rápidos."""
    video_file = tmp_path / "test_video.mp4"
    width, height = 120, 90
    fps = 30.0
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(video_file), fourcc, fps, (width, height))
    
    try:
        for i in range(15):
            # Cria um quadro com cor e forma variadas
            img = np.zeros((height, width, 3), dtype=np.uint8)
            color = ((i * 15) % 255, (i * 30) % 255, 200)
            cv2.circle(img, (20 + i * 5, 45), 15, color, -1)
            out.write(img)
    finally:
        out.release()
        
    return video_file
```

## 2. Testes Recomendados

1. **Teste de Conversão Básica**:
   - Executar `convert_file` com o arquivo sintético.
   - Verificar se o arquivo `.gif` existe na pasta de saída.
   - Validar que o GIF possui tamanho de arquivo maior que zero e pode ser aberto com `PIL.Image.open()`.
2. **Teste de Escala e Resolução**:
   - Verificar se as dimensões do GIF final correspondem à escala definida (ex: 50% de 120x90 = 60x45).
3. **Teste de Validação de Erros**:
   - Passar caminho inexistente e esperar `FileNotFoundError`.
   - Passar arquivo com extensão válida mas corrompido e verificar tratamento de exceção amigável.
4. **Teste de Isolamento Offline**:
   - Bloquear chamadas de socket com `monkeypatch` durante a execução da conversão para comprovar que nenhuma chamada de rede é tentada.

## 3. Comandos de Execução
```bash
# Executa todos os testes
poetry run pytest

# Executa testes com saída detalhada
poetry run pytest -v -s
```

# Regras do Projeto simple-gif: Melhores Práticas em Python

Estas regras devem ser seguidas rigorosamente por todos os agentes e desenvolvedores que contribuem para o projeto **simple-gif**.

## 1. Padrões de Código e Estilo
- **Python 3.12+ Idiomático**: Utilize os recursos modernos do Python 3.12+, incluindo tipagem nativa (`list[T]`, `dict[K, V]`, `T | None` em vez de `Optional[T]` do `typing`).
- **PEP 8**: Siga estritamente as convenções de nomenclatura e formatação da PEP 8:
  - Funções e variáveis em `snake_case`.
  - Classes em `PascalCase`.
  - Constantes em `UPPER_SNAKE_CASE`.
- **Imports Limpos**:
  - Organize imports de acordo com a PEP 8: biblioteca padrão, bibliotecas de terceiros e módulos locais.
  - Nunca deixe imports órfãos ou não utilizados.

## 2. Tipagem Estática (Type Hinting)
- Todas as funções e métodos públicos devem conter anotações de tipo completas em argumentos e retornos:
  ```python
  def convert_file(
      self,
      path: str | Path,
      output_path: str | Path = "outputs",
      scale: float = 0.6,
      less_colors: bool = False,
      max_frames: int = 2000,
      frame_skip: int = 5,
      progress_callback: Callable[[int, int], None] | None = None,
  ) -> Path:
  ```

## 3. Tratamento de Exceções Semântico
- **Proibido levantar tuplas com códigos de erro** (ex: `raise ValueError("msg", -1)`).
- Levante sempre exceções padrão adequadas com mensagens descritivas:
  - `FileNotFoundError`: quando o arquivo de entrada não existe.
  - `FileExistsError`: quando o GIF de destino já existe e sobrescrita não foi autorizada.
  - `ValueError`: para parâmetros inconsistentes (ex: escala <= 0, frame_skip < 1).
  - `RuntimeError`: para falhas na leitura do fluxo de vídeo ou decodificação.

## 4. Gestão de Recursos (Resource Management)
- Qualquer recurso do sistema operacional ou periférico deve ser fechado adequadamente via context manager (`with`) ou bloco `try...finally`:
  - Capturas de vídeo OpenCV: certificar-se de executar `cap.release()`.
  - Escritores de arquivo ImageIO: usar `with imageio.get_writer(...) as writer:`.
- Nunca deixe ponteiros de arquivo abertos.

## 5. Código Limpo e Manutenibilidade
- Elimine código morto: nunca mantenha funções obsoletas comentadas ou métodos duplicados não referenciados (como o antigo `_save_gif`).
- Princípio da Responsabilidade Única (SRP): separe estritamente a camada de conversão multimídia (`simplegif.py`) da interface gráfica (`app.py`).

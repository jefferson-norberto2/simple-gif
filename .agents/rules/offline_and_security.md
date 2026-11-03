# Regras de Segurança e Garantia Offline

O projeto **simple-gif** foi concebido como uma alternativa **100% offline e segura** a conversores em nuvem. A violação desses princípios compromete a proposta de valor do software.

## 1. Isolamento Offline Estrito
- **Zero Telemetria / Zero Conexão**:
  - O código não deve, sob nenhuma hipótese, realizar chamadas HTTP/HTTPS, abrir sockets de rede, consultar servidores de métricas ou tentar atualizar-se automaticamente pela internet.
  - Não adicione bibliotecas que possuam telemetria embutida ou que realizem downloads em tempo de execução (ex: download de modelos, codecs sob demanda).
  - Todos os codecs e dependências devem ser auto-contidos no ambiente local ou no executável final.

## 2. Manipulação de Arquivos e Compatibilidade Multiplataforma
- **Uso Obrigatório de `pathlib.Path`**:
  - É proibido realizar manipulação manual de caminhos usando `split('/')` ou concatenações manuais de string.
  - Utilize sempre `pathlib.Path` ou `os.path` seguro para lidar de forma consistente com Windows (`\`), Linux (`/`) e macOS (`/`).
  - Garanta que a pasta de destino exista antes de tentar salvar:
    ```python
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    ```

## 3. Validação Robusta de Entrada e Prevenção de Falhas (Hardening)
- **Validação de Fluxo de Vídeo**:
  - Sempre verifique se o arquivo de vídeo pôde ser aberto com sucesso:
    ```python
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise RuntimeError(f"Não foi possível abrir o arquivo de vídeo: {input_path}")
    ```
  - Verifique se a largura, altura e contagem de frames são maiores que zero antes de realizar operações matemáticas ou de redimensionamento.
- **Tratamento de Frames Corrompidos**:
  - Nunca assuma que todo frame lido é válido. Se `ret` for `False` ou o `frame` for `None`, encerre o laço de leitura de forma graciosa sem travar o processo.

## 4. Proteção contra Esgotamento de Memória (Anti-OOM / DoS Local)
- **Streaming de Quadros Obrigatório**:
  - Não acumule milhares de frames descompactados como arrays na memória RAM (`self._frames = []` com listas gigantes).
  - Processe e grave quadro a quadro no escritor do GIF (pipeline de streaming). Isso permite processar vídeos longos ou em alta resolução sem sobrecarregar a memória da máquina do usuário.

## 5. Execução Segura no Sistema Operacional
- Ao acionar comandos do sistema para abrir a pasta de saída (`os.startfile`, `xdg-open`, `open`):
  - Certifique-se de que o caminho apontado é um diretório válido existente (`Path(dir).is_dir()`).
  - Nunca passe strings não sanitizadas diretamente para executores com shell ativado (`shell=True` é proibido).

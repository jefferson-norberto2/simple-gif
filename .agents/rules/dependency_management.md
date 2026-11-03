# Regras de Gerenciamento de Dependências

O projeto deve ser enxuto, eficiente e livre de dependências fantasmas ou desnecessárias.

## 1. Princípio da Dependência Mínima
- Cada dependência declarada em `pyproject.toml` deve ter uma justificativa técnica clara e ser ativamente importada no código de produção.
- **Auditoria de Dependências Órfãs**:
  - Bibliotecas declaradas mas não utilizadas (ex: `jinja2`, `pyyaml`, `typeguard`, `tqdm`) devem ser removidas imediatamente para reduzir o tempo de instalação, o tamanho do executável e a superfície de ataque.
- **Separação de Dependências**:
  - Dependências de desenvolvimento e testes (ex: `pytest`, `ruff`, `mypy`) devem ser configuradas exclusivamente sob grupos de desenvolvimento (`[tool.poetry.group.dev.dependencies]`), nunca nas dependências principais do pacote de distribuição.

## 2. Redução do Tamanho do Binário Final
- Como o projeto é compilado via PyInstaller para distribuição aos usuários finais:
  - Avalie o uso de `opencv-python-headless` se os módulos de interface de janela nativa do OpenCV (HighGUI) não forem necessários.
  - Certifique-se de que o PyInstaller inclua apenas os metadados indispensáveis (ex: `--copy-metadata imageio`).

---
name: code-quality-audit
description: >-
  Use this skill when auditing the simple-gif repository for unused dependencies in pyproject.toml,
  orphaned imports, dead code, memory leaks, and compliance with Python best practices and offline security.
---

# Code Quality & Dependency Audit Skill

Este guia orienta o procedimento passo a passo para auditar o código do **simple-gif**, identificar bibliotecas desnecessárias, código morto e garantir as melhores práticas em Python.

## 1. Procedimento de Auditoria de Dependências

1. **Listar Dependências Declaradas**:
   Abra [`pyproject.toml`](file:///C:/Users/jmn/Documents/dev/python/simple-gif/pyproject.toml) e liste todas as entradas na chave `dependencies`.
2. **Escanear Imports no Código**:
   Execute uma busca textual ou estática em todos os arquivos `.py` do projeto para verificar se cada dependência é de fato importada:
   ```powershell
   # PowerShell
   Select-String -Path "simplegif\*.py", "main.py" -Pattern "nome_da_lib"
   ```
3. **Classificar Dependências**:
   - **Produção Ativa**: (ex: `opencv-python`, `Pillow`, `imageio`, `customtkinter`).
   - **Órfãs / Inúteis**: (ex: `jinja2`, `pyyaml`, `typeguard`, `tqdm`). **Ação recomendada**: remover do `pyproject.toml`.
   - **Ferramentas de Build**: `pyinstaller` (deve ser movida para grupo `[tool.poetry.group.dev.dependencies]` ou mantida como ferramenta de compilação).

## 2. Procedimento de Detecção de Código Morto

1. **Métodos Não Referenciados**:
   - Analisar classes públicas para identificar métodos duplicados ou nunca chamados externamente (ex: [`_save_gif`](file:///C:/Users/jmn/Documents/dev/python/simple-gif/simplegif/simplegif.py#L185) que permaneceu após a criação de `save_gif`).
2. **Imports Órfãos**:
   - Verificar imports no topo dos arquivos que não são utilizados no corpo do módulo.
3. **Padrão de Exceções**:
   - Procurar por tuplas em comandos `raise` (ex: `raise ValueError(..., -1)`).
   - Substituir por exceções idiomáticas do Python com mensagens claras e legíveis.

## 3. Checklist de Validação do Auditor
- [ ] O `pyproject.toml` contém apenas as dependências realmente consumidas pelo código?
- [ ] O arquivo `poetry.lock` foi sincronizado após a remoção de pacotes desnecessários?
- [ ] Todos os módulos utilizam `pathlib.Path` para caminhos de arquivo?
- [ ] Não há trechos de código morto, métodos não invocados ou imports esquecidos?
- [ ] As exceções são padronizadas e sem tuplas de código de erro?
- [ ] Há separação clara entre dependências de desenvolvimento (`pytest`, `ruff`) e de produção?

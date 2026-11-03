# Sistema Multi-Agente: simple-gif

Bem-vindo ao sistema de agentes e customizações do projeto **simple-gif**.

Este projeto tem como meta central ser uma ferramenta **100% offline, segura, leve e eficiente** para conversão de vídeos em GIFs animados com alta qualidade.

---

## 1. Agentes Especializados

| Agente | Arquivo de Definição | Função Principal |
| :--- | :--- | :--- |
| **Feature Agent** | [`.agents/subagents/feature.md`](file:///C:/Users/jmn/Documents/dev/python/simple-gif/.agents/subagents/feature.md) | Implementa funcionalidades no motor de vídeo, interface gráfica CustomTkinter e CLI. |
| **Test Agent** | [`.agents/subagents/test.md`](file:///C:/Users/jmn/Documents/dev/python/simple-gif/.agents/subagents/test.md) | Cria e executa testes com `pytest` usando fixtures de vídeo sintético e validação de regressão. |
| **QA Agent** | [`.agents/subagents/qa.md`](file:///C:/Users/jmn/Documents/dev/python/simple-gif/.agents/subagents/qa.md) | Audita conformidade com PEP 8, busca código morto, detecta bibliotecas não utilizadas e valida a postura offline. |

---

## 2. Regras do Workspace (`rules/`)

As regras são aplicadas automaticamente pelo sistema Antigravity em todas as operações:

- [**`python_best_practices.md`**](file:///C:/Users/jmn/Documents/dev/python/simple-gif/.agents/rules/python_best_practices.md): Convenções da PEP 8, tipagem com Python 3.12+, tratamento semântico de exceções e eliminação de código morto.
- [**`offline_and_security.md`**](file:///C:/Users/jmn/Documents/dev/python/simple-gif/.agents/rules/offline_and_security.md): Proibição absoluta de telemetria ou acessos de rede, uso obrigatório de `pathlib.Path`, prevenção de esgotamento de memória (streaming de quadros) e segurança de subprocessos.
- [**`dependency_management.md`**](file:///C:/Users/jmn/Documents/dev/python/simple-gif/.agents/rules/dependency_management.md): Manutenção de dependências mínimas, proibição de pacotes órfãos e separação rigorosa de pacotes de desenvolvimento.

---

## 3. Catálogo de Skills (`skills/`)

- [**`video-gif-core`**](file:///C:/Users/jmn/Documents/dev/python/simple-gif/.agents/skills/video-gif-core/SKILL.md): Padrões de streaming OpenCV $\rightarrow$ ImageIO, controle de FPS e quantização adaptativa.
- [**`synthetic-video-testing`**](file:///C:/Users/jmn/Documents/dev/python/simple-gif/.agents/skills/synthetic-video-testing/SKILL.md): Criação de fixtures sintéticas para testes rápidos e determinísticos com `pytest`.
- [**`code-quality-audit`**](file:///C:/Users/jmn/Documents/dev/python/simple-gif/.agents/skills/code-quality-audit/SKILL.md): Auditoria passo a passo de dependências órfãs, imports não utilizados e boas práticas Python.

# simple-gif: Workspace Agent Directives

Este repositório utiliza o sistema de agentes do Antigravity localizado em [`.agents/`](file:///C:/Users/jmn/Documents/dev/python/simple-gif/.agents).

## Princípios Centrais
1. **100% Offline & Seguro**: Nenhuma chamada de rede, telemetria ou serviços externos é permitida.
2. **Compatibilidade Multiplataforma**: Usar exclusivamente `pathlib.Path` para manipulação de arquivos.
3. **Eficiência de Recursos**: Processamento de quadros em streaming para evitar consumo excessivo de RAM.
4. **Dependências Mínimas**: Eliminar pacotes órfãos e manter apenas as bibliotecas essenciais para o funcionamento local.

Para detalhes completos sobre os agentes, regras e skills, consulte [`.agents/AGENTS.md`](file:///C:/Users/jmn/Documents/dev/python/simple-gif/.agents/AGENTS.md).

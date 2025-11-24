# AGENTS.md

## Review guidelines
- Verificar que nenhuma rota pública fique sem autenticação.
- Garantir que novas funcionalidades tenham cobertura mínima de testes (ex: 80% ou conforme equipe definir).
- Não logar dados pessoais identificáveis (PII) ou informações confidenciais.
- Manter o padrão de nomenclatura da equipe (por exemplo camelCase para variáveis, PascalCase para classes).
- Evitar uso de dependências obsoletas ou vulneráveis — checar se há alertas de segurança/transitive dependencies.
- Avaliar performance nas mudanças: evitar loops aninhados sem necessidade, operações de I/O intensivo sem caching quando for crítico.
- Revisar modularização: o código novo ou alterado deve seguir a estrutura de pastas da equipe (ex: `/src/modules/`, `/tests/`).
- Comentários e documentação: se a mudança adiciona comportamento novo, verificar se há testes e/ou documentação associada.

## Special instruction example
Para solicitações específicas, você pode comentar no PR:
`@codex review for security regressions`
O agente irá priorizar o foco em segurança para aquela revisão.

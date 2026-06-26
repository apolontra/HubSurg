# Documentação — HubSurg

Documentação de arquitetura do **Dossiê Cirúrgico Centralizado**.

## Índice

### Arquitetura
- [Visão geral da arquitetura](architecture/overview.md)
- [Modelo de dados](architecture/data-model.md)
- [Decisões de arquitetura (ADRs)](architecture/adr/README.md)

### Interoperabilidade
- [Mapeamento de recursos FHIR](fhir/resource-mapping.md)

### Segurança e conformidade
- [Privacidade e cibersegurança](security/privacy-and-security.md)

## Convenções

- Diagramas usam [Mermaid](https://mermaid.js.org/) e renderizam diretamente no GitHub.
- Decisões com impacto estrutural são registradas como **ADR** (Architecture Decision Record),
  seguindo o formato de Michael Nygard.
- Os documentos descrevem o **alvo de arquitetura**; o estado de implementação é sinalizado
  explicitamente quando diverge do alvo.

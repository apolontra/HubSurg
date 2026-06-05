# HubSurg

**Dossiê Cirúrgico Centralizado** — plataforma que consolida o histórico clínico-cirúrgico
do paciente (exames, laudos, checklists pré/pós-operatórios e planos de cuidado) em um
único dossiê, com **interoperabilidade by design** via **HL7 FHIR**.

> Status atual: **fundação de arquitetura**. Este repositório contém, neste momento, a
> documentação de arquitetura que orienta a construção do MVP. Ainda não há código de
> aplicação.

## Documentação

A documentação vive em [`docs/`](docs/README.md). Pontos de partida:

| Documento | Descrição |
|-----------|-----------|
| [Visão geral da arquitetura](docs/architecture/overview.md) | Frontend, backend hexagonal, mensageria e princípios de engenharia |
| [Modelo de dados](docs/architecture/data-model.md) | Esquema híbrido PostgreSQL + pgvector, índices e particionamento |
| [Mapeamento FHIR](docs/fhir/resource-mapping.md) | Como o dossiê é representado como recursos HL7 FHIR |
| [Privacidade e cibersegurança](docs/security/privacy-and-security.md) | LGPD/GDPR/CFM, criptografia, AuthN/AuthZ, logs |
| [Decisões de arquitetura (ADRs)](docs/architecture/adr/README.md) | Registro das decisões e seus trade-offs |

## Princípios norteadores

1. **Interoperabilidade by design** — o modelo canônico interno é mapeável para FHIR R4.
2. **Privacidade por padrão** — minimização de dados, criptografia em repouso e em trânsito.
3. **Arquitetura desacoplada** — domínio clínico isolado de frameworks e fornecedores.
4. **Evolutividade** — começar enxuto (MVP) sem fechar portas para escala.

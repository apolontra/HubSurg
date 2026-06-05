# ADR-0006 — Camada de segurança (auth, RBAC, rate limiting)

- **Status:** Aceito
- **Data:** 2026-06-05

## Contexto

O Dossiê Cirúrgico trata dados sensíveis de saúde; sob LGPD, autenticação, autorização e
controles de borda são pré-requisitos para manipular esses dados (ver
[privacidade e cibersegurança](../../security/privacy-and-security.md)). O backend precisava
sair de "aberto" para uma postura mínima segura, mantendo a fundação enxuta e sem infra
externa.

Restrição prática do ambiente: bibliotecas nativas de criptografia (`cryptography`, `bcrypt`,
`pyjwt`) estavam indisponíveis (faltava `_cffi_backend`), impedindo seu uso imediato.

## Decisão

Implementar a camada de segurança **apenas com a biblioteca padrão**, atrás de ports do
domínio:

- **Autenticação:** JWT **HS256** assinado com `hmac`/`hashlib` (port `TokenService`),
  emitido em `POST /auth/token`.
- **Senhas:** **PBKDF2-HMAC-SHA256** com sal e fator de trabalho (port `PasswordHasher`) —
  um KDF de senha legítimo, ao contrário de SHA-256 "cru".
- **RBAC:** papéis `surgeon`/`assistant`/`admin` (entidade `User`, `Role`), aplicados por
  uma dependência `require_roles(...)` na borda HTTP.
- **Borda:** middlewares de **rate limiting** (janela fixa por IP, em memória) e de
  **cabeçalhos de proteção** (CSP, HSTS, X-Frame-Options, X-Content-Type-Options).

## Alternativas consideradas

- **bcrypt/argon2 + pyjwt (RS256)** — preferíveis em produção, mas bloqueados pelo ambiente
  atual. Como tudo está atrás de ports, a troca é localizada e não toca domínio/aplicação.
- **Adiar segurança** — inaceitável para dados de saúde, mesmo em MVP.

## Consequências

- **Positivas:** postura mínima segura sem dependências nativas nem infra; ports permitem
  evoluir para bibliotecas dedicadas sem refatorar; controles testados (16 testes de
  segurança/API).
- **Negativas / limites conscientes (produção):**
  - HS256 usa segredo compartilhado — migrar para **RS256** com rotação de chaves.
  - Substituir PBKDF2 por **bcrypt/argon2** quando as libs estiverem disponíveis.
  - Rate limiting em memória não é compartilhado entre réplicas — usar **Redis** ou o
    limitador da borda (Nginx/WAF).
  - **2FA** (exigido para cirurgiões) e **CSRF** ainda são pontos do plano, não implementados.
  - Usuários são *seed* in-memory — substituir por diretório/IdP.

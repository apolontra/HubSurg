# HubSurg — Frontend

Scaffold do frontend **Next.js (App Router) + TypeScript**, seguindo o ADR-0005
(SSR para telas críticas, CSR para conteúdo assíncrono; componentes em Atomic Design).

> Estado: scaffold inicial. Conecta-se ao backend (`../backend`) via HTTPS/REST.

## Como rodar

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
```

## Qualidade — ritual de precheck

Antes de abrir um PR (espelha o CI). Ordem do mais barato/rápido ao mais caro; o `&&` faz
**parar no primeiro erro**:

```bash
npm run precheck   # typecheck (tsc --noEmit) → lint (next lint) → build (next build)
```

Alvos individuais:

```bash
npm run typecheck
npm run lint
npm run build
```

> Nota: `next lint` será descontinuado no Next 16. Este scaffold usa Next 14, onde ele
> funciona com `eslint-config-next`. Ao migrar para o Next 15+, troque para `eslint .`.

## Estrutura

```
app/                     # App Router (layout, páginas)
components/atoms/         # Atomic Design — átomos reutilizáveis
```

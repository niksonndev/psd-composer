# Gadget Imports Store – Playground Hydrogen

Este repositório é um **playground de Hydrogen** criado para:

- **Explorar funcionalidades do Hydrogen + Remix + Oxygen**
- **Testar integrações e APIs da Shopify (Storefront / Customer Account API)**
- **Servir como preparação para entrevistas**, simulando um projeto real de storefront headless

Não é um template genérico; é um ambiente de experimentação. O código pode conter rotas e componentes apenas para teste de features, sem compromisso com design ou UX finais.

## Tech stack

- Hydrogen (Shopify)
- Remix / React Router
- Oxygen / Mini-Oxygen
- Vite
- TypeScript
- ESLint + Prettier

## Requisitos

- Node.js `>= 18.0.0`
- pnpm (o projeto usa `pnpm` como package manager)

## Instalação

```bash
pnpm install
```

## Scripts

- `pnpm run dev` – servidor de desenvolvimento
- `pnpm run build` – build de produção
- `pnpm run preview` – preview do build
- `pnpm run lint` – lint do código
- `pnpm run typecheck` – typecheck com TypeScript

## Notas de ambiente

- Copie `.env.example` para `.env` e preencha os valores:

```bash
cp .env.example .env
```

- É obrigatório definir um `SESSION_SECRET` válido, senão o app lança erro ao iniciar (sessões de usuário).

## Links úteis

- Docs Hydrogen: https://shopify.dev/custom-storefronts/hydrogen
- Docs Remix / React Router: https://reactrouter.com

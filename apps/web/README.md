# Credit cabinet frontend

React + TypeScript + Vite, Alfa Core Components. Standalone local demonstration,
no API server, real bank integrations or authentication. All data is synthetic.

```sh
npm ci --ignore-scripts
npm run dev
```

Open http://127.0.0.1:4180. Node 22.12+ required (verified with 22.22.2).
From the repository root: `docker compose -f compose.frontend.yaml up --build`.
Stop the dev server first: Docker uses the same host port.

```sh
npm test
npm run build
npm run preview -- --port 4180 --strictPort
```

See [frontend specification](../../docs/frontend.md) for routes, source material,
UI decisions, state boundaries and known limits. See
[verification](../../docs/frontend-verification.md) for actual test coverage.

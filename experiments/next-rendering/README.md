# Next.js rendering lab

Use the same fictional garden to compare build-time HTML, request-time HTML and
a browser interaction. This optional experiment runs in its own Next.js App
Router package with a separate npm lockfile.

From the repository root, use Node 20.9 or newer:

```sh
cd experiments/next-rendering
npm ci
npm run typecheck
npm run build
npm run start
```

Open [the lab](http://127.0.0.1:4175). Both `dev` and `start` bind to loopback
on port 4175 and disable Next.js telemetry. Use the production build to compare
cache behavior. `npm run dev` is useful when editing the experiment.

| View | What to try | Expected behavior |
| --- | --- | --- |
| `/` | Select **Request again** | The render ID and UTC time stay the same until you build again. Next labels this route `○ Static`. |
| `/request-time` | Select **Request again** | Next awaits a request with `connection()` and renders a new ID and UTC time. Next labels this route `ƒ Dynamic`. |
| Domain filter on either page | Select **career** | The browser displays one of the four notes. The render ID stays the same. |

Both pages ship the complete initial note view in their HTML. The shared server
component reads [the fictional seed](../../examples/mock-garden/world.json) and
passes display fields to the client component. The experiment uses the existing
fixture directly and has no API route, external dependency at runtime, or
configuration for private gardens.

To check the values without a browser, request each route twice against the
production server:

```sh
for path in / /request-time; do
  for request in 1 2; do
    curl --fail --silent --show-error "http://127.0.0.1:4175${path}" |
      rg --only-matching 'data-render-id="">[^<]+'
  done
done
```

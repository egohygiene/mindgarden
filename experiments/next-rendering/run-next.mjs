import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
process.env.NEXT_TELEMETRY_DISABLED = "1";
process.argv[1] = require.resolve("next/dist/bin/next");
require(process.argv[1]);

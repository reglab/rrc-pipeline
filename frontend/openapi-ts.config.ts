import { defineConfig } from "@hey-api/openapi-ts";

const args = process.argv.slice(2);
const host = args[0] || "poirot:8101";

export default defineConfig({
  client: "@hey-api/client-fetch",
  input: host.includes("http")
    ? `${host}/openapi.json`
    : `http://${host}/openapi.json`,
  output: {
    path: "src/client",
    format: "biome",
  },
  plugins: [
    "@tanstack/react-query",
    {
      name: "@hey-api/transformers",
      dates: true,
    },
    {
      name: "@hey-api/services",
      asClass: true,
    },
    {
      name: "@hey-api/types",
      enums: "javascript",
    },
  ],
});

import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  input: "./openapi.json",
  output: {
    path: "./src/client",
  },
  plugins: ["@hey-api/client-fetch"],
});

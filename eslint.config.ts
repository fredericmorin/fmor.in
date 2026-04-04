import eslint from "@eslint/js";
import tseslint from "typescript-eslint";
import pluginVue from "eslint-plugin-vue";

export default tseslint.config(
  eslint.configs.recommended,
  tseslint.configs.recommended,
  pluginVue.configs["flat/essential"],
  {
    files: ["**/*.vue"],
    languageOptions: {
      parserOptions: {
        parser: tseslint.parser,
      },
    },
  },
  {
    // TypeScript handles browser globals via lib: ["DOM"] — no need to re-check them here.
    rules: {
      "no-undef": "off",
    },
  },
  {
    ignores: ["static/dist/**", "output/**", "node_modules/**"],
  },
);

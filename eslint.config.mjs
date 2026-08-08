import js from "@eslint/js";
import globals from "globals";

export default [
  js.configs.recommended,

  // 1. Global settings for ALL JavaScript files (including tests)
  {
    files: ["**/*.js"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "commonjs",
      globals: {
        ...globals.node,
        URL: "readonly",
        FormData: "readonly",
      },
    },
    rules: {
      "no-unused-vars": [
        "error",
        {
          "argsIgnorePattern": "^_", // Ignores unused arguments (e.g., function(_, res))
          "varsIgnorePattern": "^_", // Ignores unused variables (e.g., const _ = ...)
        }
      ]
    }
  },

  // 2. Additional layer strictly for test files to add Jest globals
  {
    files: ["**/tests/**/*.js", "**/*.test.js", "**/*.property.test.js"],
    languageOptions: {
      globals: {
        ...globals.jest,
      },
    },
    // Duplicating the rule here guarantees it forces compliance inside test files
    rules: {
      "no-unused-vars": [
        "error",
        {
          "argsIgnorePattern": "^_",
          "varsIgnorePattern": "^_"
        }
      ]
    }
  }
];

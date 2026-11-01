// ESLint flat config（ESLint 10）——质量门：TS + Vue + 模块边界（boundaries v7）+ Prettier
import pluginVue from "eslint-plugin-vue";
import tseslint from "typescript-eslint";
import boundaries from "eslint-plugin-boundaries";
import prettierSkip from "eslint-config-prettier";

export default [
  {
    ignores: ["dist/**", "src-tauri/**", "node_modules/**", "coverage/**", "*.log"],
  },

  ...tseslint.configs.recommended,
  ...pluginVue.configs["flat/recommended"],

  {
    files: ["**/*.vue"],
    languageOptions: {
      parserOptions: {
        parser: tseslint.parser,
      },
    },
  },

  {
    files: ["**/*.{ts,vue}"],
    plugins: { boundaries },
    settings: {
      // TS 解析器：让 boundaries 能解析无扩展名导入与 @ 路径别名
      "import/resolver": {
        typescript: {
          alwaysTryTypes: true,
        },
      },
      // 元素类型 = 架构分层，路径相对项目根（对齐 v2 目录树）
      "boundaries/elements": [
        { type: "app", pattern: "src/app/**" },
        { type: "core", pattern: "src/core/**" },
        { type: "shared", pattern: "src/shared/**" },
        { type: "services", pattern: "src/services/**" },
        { type: "feature", pattern: "src/features/**" },
        { type: "data", pattern: "src/assets/data/**" },
      ],
    },
    rules: {
      // 默认禁止，按白名单单向放行（依赖倒置，无环）——v7 语法
      "boundaries/dependencies": [
        "error",
        {
          default: "disallow",
          policies: [
            // 入口/装配可引用一切
            {
              from: { element: { type: "app" } },
              allow: [
                { to: { element: { type: "core" } } },
                { to: { element: { type: "shared" } } },
                { to: { element: { type: "services" } } },
                { to: { element: { type: "feature" } } },
                { to: { element: { type: "data" } } },
              ],
            },
            // feature 只向下依赖，禁止 feature 互引
            {
              from: { element: { type: "feature" } },
              allow: [
                { to: { element: { type: "core" } } },
                { to: { element: { type: "shared" } } },
                { to: { element: { type: "services" } } },
                { to: { element: { type: "data" } } },
              ],
            },
            // services：端口/适配器/导入器引用 core 契约与 shared 工具
            {
              from: { element: { type: "services" } },
              allow: [
                { to: { element: { type: "core" } } },
                { to: { element: { type: "shared" } } },
                { to: { element: { type: "services" } } },
              ],
            },
            // core：内部自洽 + shared 工具 + services 端口（CheckinStore 注入 StoragePort）
            {
              from: { element: { type: "core" } },
              allow: [
                { to: { element: { type: "core" } } },
                { to: { element: { type: "shared" } } },
                { to: { element: { type: "services" } } },
              ],
            },
            // shared 只依赖 shared
            {
              from: { element: { type: "shared" } },
              allow: [{ to: { element: { type: "shared" } } }],
            },
          ],
        },
      ],
      "boundaries/no-unknown-dependencies": "error",
      "boundaries/no-ignored-dependencies": "error",
    },
  },

  // 放在最后：关闭与 Prettier 冲突的规则
  prettierSkip,
];

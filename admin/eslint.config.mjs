import nextConfig from "eslint-config-next";
import coreWebVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";

const eslintConfig = [
  {
    ignores: [
      ".next/**",
      "node_modules/**",
      "out/**",
      "next-env.d.ts",
      "eslint.config.mjs",
    ],
  },
  ...nextConfig,
  ...coreWebVitals,
  ...nextTypescript,
  {
    rules: {
      // The new react-hooks v7 rule flags every `useEffect(() => {
      // fetch().then(setState) }, [])` data-fetching pattern. We rely on
      // it heavily until we migrate to React 19's `use()` + Suspense.
      "react-hooks/set-state-in-effect": "off",
      // eslint-plugin-react currently trips on ESLint 10's flat-config context
      // while resolving the React version. Next.js already handles component
      // display names through its defaults and TypeScript coverage here.
      "react/display-name": "off",
    },
  },
];

export default eslintConfig;

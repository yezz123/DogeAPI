import nextConfig from "eslint-config-next";
import coreWebVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";

const eslintConfig = [
  ...nextConfig,
  ...coreWebVitals,
  ...nextTypescript,
  {
    rules: {
      // The new react-hooks v7 rule flags every `useEffect(() => {
      // fetch().then(setState) }, [])` data-fetching pattern. We rely on
      // it heavily until we migrate to React 19's `use()` + Suspense.
      "react-hooks/set-state-in-effect": "off",
    },
  },
  {
    ignores: [".next/**", "node_modules/**", "out/**", "next-env.d.ts"],
  },
];

export default eslintConfig;

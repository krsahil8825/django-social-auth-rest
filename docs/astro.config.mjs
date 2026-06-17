import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";
import starlightThemeGalaxy from "starlight-theme-galaxy";

import sitemap from "@astrojs/sitemap";

export default defineConfig({
  site: "https://krsahil8825.github.io",
  base: "/django-social-auth-rest",
  integrations: [
    starlight({
      title: "Django Social Auth Rest",
      favicon: "/favicon.png",
      plugins: [starlightThemeGalaxy()],
      social: [
        { icon: "github", label: "GitHub", href: "https://github.com/krsahil8825/django-social-auth-rest" },
        { icon: "seti:python", label: "PyPI", href: "https://pypi.org/project/django-social-auth-rest/" },
      ],
      sidebar: [{ label: "Guides", items: [{ autogenerate: { directory: "guides" } }], collapsed: true }],
    }),
    sitemap(),
  ],
});

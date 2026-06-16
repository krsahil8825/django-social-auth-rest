// @ts-check
import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";
import starlightThemeGalaxy from "starlight-theme-galaxy";

// https://astro.build/config
export default defineConfig({
  integrations: [
    starlight({
      title: "Django Social Auth Rest",
      plugins: [starlightThemeGalaxy()],
      social: [{ icon: "github", label: "GitHub", href: "https://github.com/krsahil8825/django-social-auth-rest" }],
      sidebar: [{ label: "Guides", items: [{ autogenerate: { directory: "guides" } }], collapsed: true }],
    }),
  ],
});

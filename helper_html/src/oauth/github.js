const BACKEND_BASE_URL = import.meta.env.VITE_BACKEND_BASE_URL;
const GITHUB_CLIENT_ID = import.meta.env.VITE_GITHUB_CLIENT_ID;
const GITHUB_REDIRECT_URI = import.meta.env.VITE_GITHUB_REDIRECT_URI;

export async function githubLogin() {
  try {
    const response = await fetch(`${BACKEND_BASE_URL}social-auth/github/state/`);

    if (!response.ok) {
      throw new Error("Failed to fetch OAuth state.");
    }

    const data = await response.json();

    const state = data.state;

    console.log("Received State:", state);

    const githubUrl =
      `https://github.com/login/oauth/authorize` +
      `?client_id=${GITHUB_CLIENT_ID}` +
      `&redirect_uri=${encodeURIComponent(GITHUB_REDIRECT_URI)}` +
      `&scope=user:email` +
      `&state=${encodeURIComponent(state)}`;

    window.location.href = githubUrl;
  } catch (error) {
    console.error(error);
  }
}

export function handleGithubLogin() {
  const params = new URLSearchParams(window.location.search);

  const code = params.get("code");
  const state = params.get("state");

  if (!code || !state) {
    return;
  }

  console.log("GitHub Code:", code);
  console.log("GitHub State:", state);
}

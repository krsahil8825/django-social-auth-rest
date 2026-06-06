import { initializeGoogleAuth } from "./oauth/google";
import { githubLogin, handleGithubLogin } from "./oauth/github";

window.addEventListener("load", () => {
  initializeGoogleAuth();

  handleGithubLogin();

  const githubButton = document.getElementById("github-button");

  githubButton?.addEventListener("click", githubLogin);
});

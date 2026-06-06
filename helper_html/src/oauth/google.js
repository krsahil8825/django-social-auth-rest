function handleGoogleLogin(response) {
  console.log("Google Token:", response.credential);
}

export function initializeGoogleAuth() {
  google.accounts.id.initialize({
    client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
    callback: handleGoogleLogin,
  });

  google.accounts.id.renderButton(document.getElementById("google-button"), {
    theme: "outline",
    size: "large",
    width: 250,
  });
}

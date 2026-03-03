export function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return Date.now() >= payload.exp * 1000;
  } catch {
    return true;
  }
}

export function validateTokenAndRedirect(): boolean {
  // DISABLED: Auth checks are disabled per system memory
  // Return true to prevent redirect to /auth
  return true;
}

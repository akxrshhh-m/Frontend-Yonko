const BASE_URL =
  (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_URL) ||
  (typeof process !== 'undefined' && process.env && process.env.REACT_APP_API_URL) ||
  'http://localhost:5000';

export async function apiRequest(endpoint, options = {}) {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  const cleanBase = BASE_URL.endsWith('/') ? BASE_URL.slice(0, -1) : BASE_URL;
  const url = cleanBase + '/' + cleanEndpoint;
  const headers = Object.assign({ 'Content-Type': 'application/json' }, options.headers || {});
  const response = await fetch(url, Object.assign({}, options, { headers }));
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.message || ('API Error: ' + response.statusText));
  }
  return response.json();
}
export default apiRequest;

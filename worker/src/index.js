const SESSION_COOKIE = "ci_session";
const SESSION_TTL_SECONDS = 60 * 60 * 12;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/health") return json({ ok: true, mode: "proxy" });
    if (url.pathname === "/login" && request.method === "GET") return html(loginPage());
    if (url.pathname === "/login" && request.method === "POST") return login(request, env);
    if (url.pathname === "/logout") return logout();

    if (!(await isAuthed(request, env))) {
      if (url.pathname.startsWith("/api/")) return json({ error: "Unauthorized" }, 401);
      return Response.redirect(`${url.origin}/login`, 302);
    }

    return proxyToOrigin(request, env);
  },
};

async function login(request, env) {
  if (!env.ADMIN_PASSWORD || !env.SESSION_SECRET) {
    return html(loginPage("Server auth is not configured."), 500);
  }
  const form = await request.formData();
  const password = String(form.get("password") || "");
  if (password !== env.ADMIN_PASSWORD) return html(loginPage("Invalid password."), 401);

  const expires = Math.floor(Date.now() / 1000) + SESSION_TTL_SECONDS;
  const value = await signSession(expires, env.SESSION_SECRET);
  return new Response(null, {
    status: 302,
    headers: {
      Location: "/",
      "Set-Cookie": `${SESSION_COOKIE}=${value}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=${SESSION_TTL_SECONDS}`,
    },
  });
}

function logout() {
  return new Response(null, {
    status: 302,
    headers: {
      Location: "/login",
      "Set-Cookie": `${SESSION_COOKIE}=; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=0`,
    },
  });
}

async function proxyToOrigin(request, env) {
  if (!env.ORIGIN_URL || !env.ORIGIN_BASIC_AUTH) {
    return html(loginPage("Origin proxy is not configured."), 500);
  }
  const incoming = new URL(request.url);
  const target = new URL(env.ORIGIN_URL);
  target.pathname = incoming.pathname;
  target.search = incoming.search;

  const headers = new Headers(request.headers);
  headers.set("Authorization", `Basic ${env.ORIGIN_BASIC_AUTH}`);
  headers.set("Host", target.host);
  headers.delete("Cookie");

  const init = {
    method: request.method,
    headers,
    body: ["GET", "HEAD"].includes(request.method) ? undefined : request.body,
    redirect: "manual",
  };
  const response = await fetch(target, init);
  const proxyHeaders = new Headers(response.headers);
  proxyHeaders.delete("WWW-Authenticate");
  proxyHeaders.delete("Set-Cookie");
  proxyHeaders.set("Cache-Control", "no-store");

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: proxyHeaders,
  });
}

async function isAuthed(request, env) {
  const cookies = parseCookies(request.headers.get("Cookie") || "");
  const session = cookies[SESSION_COOKIE];
  if (!session || !env.SESSION_SECRET) return false;
  const [expiresText, signature] = session.split(".");
  const expires = Number(expiresText);
  if (!expires || expires < Math.floor(Date.now() / 1000)) return false;
  const expected = await hmac(expiresText, env.SESSION_SECRET);
  return timingSafeEqual(signature, expected);
}

async function signSession(expires, secret) {
  const expiresText = String(expires);
  return `${expiresText}.${await hmac(expiresText, secret)}`;
}

async function hmac(value, secret) {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(value));
  return [...new Uint8Array(signature)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function timingSafeEqual(a = "", b = "") {
  if (a.length !== b.length) return false;
  let result = 0;
  for (let i = 0; i < a.length; i += 1) result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return result === 0;
}

function parseCookies(header) {
  return Object.fromEntries(header.split(";").map((part) => {
    const [key, ...rest] = part.trim().split("=");
    return [key, rest.join("=")];
  }).filter(([key]) => key));
}

function json(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
  });
}

function html(body, status = 200) {
  return new Response(body, {
    status,
    headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" },
  });
}

function loginPage(error = "") {
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Component Inventory</title>
  <style>
    :root{color-scheme:light;--bg:#f5f6f8;--panel:#fff;--ink:#1f2328;--muted:#667085;--line:#d9dee7;--accent:#0f766e;--danger:#a12f2f;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
    *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink)}
    main{min-height:100vh;display:grid;place-items:center;padding:20px}
    form{width:min(360px,100%);display:grid;gap:14px;background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:18px}
    h1,p{margin:0}h1{font-size:24px;letter-spacing:0}.lede{color:var(--muted);font-size:14px}.error{color:var(--danger);font-size:13px}
    label{display:grid;gap:6px;font-size:12px;font-weight:700}input{min-height:40px;border:1px solid var(--line);border-radius:6px;padding:0 10px;font:inherit}
    button{min-height:40px;border:0;border-radius:6px;background:var(--accent);color:#fff;font-weight:700;cursor:pointer}
  </style>
</head>
<body>
  <main>
    <form method="post" action="/login">
      <h1>Component Inventory</h1>
      <p class="lede">Remote live dashboard</p>
      ${error ? `<p class="error">${escapeHtml(error)}</p>` : ""}
      <label>Password<input name="password" type="password" autocomplete="current-password" autofocus required></label>
      <button type="submit">Sign in</button>
    </form>
  </main>
</body>
</html>`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

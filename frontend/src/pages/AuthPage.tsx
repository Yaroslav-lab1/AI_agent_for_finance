import { FormEvent, useState } from "react";
import { errorMessage } from "../api/client";
import { login, me, register } from "../api";
import type { User } from "../types/api";

const usernamePattern = /^[a-zA-Z0-9_]{3,32}$/;

export function AuthPage({ onAuth }: { onAuth: (user: User) => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("demo@example.com");
  const [username, setUsername] = useState("demo_user");
  const [displayName, setDisplayName] = useState("Демо пользователь");
  const [password, setPassword] = useState("demo-password-123");
  const [passwordRepeat, setPasswordRepeat] = useState("demo-password-123");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }
    setBusy(true);
    try {
      if (mode === "register") {
        await register({
          email,
          username,
          display_name: displayName,
          password,
        });
      }
      const token = await login(email, password);
      localStorage.setItem("access_token", token);
      onAuth(await me());
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  function validateForm(): string {
    if (password.length < 8) {
      return "Пароль должен быть не короче 8 символов";
    }
    if (mode === "register") {
      if (displayName.trim().length < 2) {
        return "Имя должно содержать минимум 2 символа";
      }
      if (!usernamePattern.test(username)) {
        return "Логин: 3-32 символа, только латиница, цифры и подчёркивание";
      }
      if (password !== passwordRepeat) {
        return "Пароли не совпадают";
      }
    }
    return "";
  }

  return (
    <main className="auth-shell">
      <form className="auth-panel" onSubmit={submit}>
        <div>
          <h1>Finance AI Agent</h1>
          <p className="auth-subtitle">
            {mode === "login" ? "Войдите в свой финансовый профиль" : "Создайте профиль для персонального учёта"}
          </p>
        </div>
        <div className="segmented">
          <button type="button" className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>
            Вход
          </button>
          <button type="button" className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>
            Регистрация
          </button>
        </div>

        {mode === "register" && (
          <>
            <label>
              Имя
              <input value={displayName} maxLength={120} onChange={(e) => setDisplayName(e.target.value)} required />
              <span className="hint">Как показывать вас в интерфейсе, например “Анна Иванова”.</span>
            </label>
            <label>
              Логин
              <input value={username} maxLength={32} onChange={(e) => setUsername(e.target.value)} required />
              <span className="hint">3-32 символа: латинские буквы, цифры и подчёркивание.</span>
            </label>
          </>
        )}

        <label>
          Email
          <input value={email} type="email" onChange={(e) => setEmail(e.target.value)} required />
          <span className="hint">Нужен для входа и восстановления доступа. Пример: name@example.com.</span>
        </label>
        <label>
          Пароль
          <input value={password} type="password" minLength={8} onChange={(e) => setPassword(e.target.value)} required />
          <span className="hint">Минимум 8 символов. Лучше использовать буквы, цифры и спецсимволы.</span>
        </label>

        {mode === "register" && (
          <label>
            Повторите пароль
            <input value={passwordRepeat} type="password" minLength={8} onChange={(e) => setPasswordRepeat(e.target.value)} required />
            <span className="hint">Повтор нужен, чтобы исключить опечатку при создании аккаунта.</span>
          </label>
        )}

        {error && <p className="error">{error}</p>}
        <button className="primary" disabled={busy}>
          {busy ? "Подождите..." : mode === "register" ? "Создать аккаунт" : "Войти"}
        </button>
      </form>
    </main>
  );
}

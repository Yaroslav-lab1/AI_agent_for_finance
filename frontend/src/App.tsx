import { useEffect, useState } from "react";
import { AuthPage } from "./pages/AuthPage";
import { DashboardPage } from "./pages/DashboardPage";
import { me } from "./api";
import type { User } from "./types/api";

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(Boolean(localStorage.getItem("access_token")));

  useEffect(() => {
    if (!localStorage.getItem("access_token")) return;
    me()
      .then(setUser)
      .catch(() => localStorage.removeItem("access_token"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <main className="center">Загрузка...</main>;
  if (!user) return <AuthPage onAuth={setUser} />;
  return <DashboardPage user={user} onLogout={() => { localStorage.removeItem("access_token"); setUser(null); }} />;
}

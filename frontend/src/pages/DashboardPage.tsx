import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import * as api from "../api";
import { errorMessage } from "../api/client";
import type { Category, ImportCandidate, ImportPreview, Transaction, User } from "../types/api";

const today = new Date().toISOString().slice(0, 10);

export function DashboardPage({ user, onLogout }: { user: User; onLogout: () => void }) {
  const qc = useQueryClient();
  const [error, setError] = useState("");
  const [filters, setFilters] = useState<Record<string, string>>({});
  const categories = useQuery({ queryKey: ["categories"], queryFn: api.categories });
  const txs = useQuery({ queryKey: ["transactions", filters], queryFn: () => api.transactions(filters) });
  const summary = useQuery({ queryKey: ["summary"], queryFn: api.summary });
  const expenses = useQuery({ queryKey: ["expenses"], queryFn: api.expensesByCategory });
  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["transactions"] });
    qc.invalidateQueries({ queryKey: ["summary"] });
    qc.invalidateQueries({ queryKey: ["expenses"] });
  };

  return (
    <main>
      <header className="topbar">
        <h1>Finance AI Agent</h1>
        <div><span>{user.display_name || user.email}</span><button onClick={onLogout}>Выйти</button></div>
      </header>
      {error && <div className="banner">{error}<button onClick={() => setError("")}>×</button></div>}
      <section className="summary">
        <Metric label="Доход" value={summary.data?.income_total ?? "0.00"} tone="good" />
        <Metric label="Расход" value={summary.data?.expense_total ?? "0.00"} tone="bad" />
        <Metric label="Баланс" value={summary.data?.balance ?? "0.00"} tone="neutral" />
      </section>
      <section className="grid">
        <TransactionForm categories={categories.data ?? []} onDone={refresh} onError={(e) => setError(errorMessage(e))} />
        <ImportPanel categories={categories.data ?? []} onDone={refresh} onError={(e) => setError(errorMessage(e))} />
      </section>
      <section className="panel">
        <h2>Расходы по категориям</h2>
        {(expenses.data?.length ?? 0) > 0 ? (
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={expenses.data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="category_name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="amount" fill="#2f7d68" />
            </BarChart>
          </ResponsiveContainer>
        ) : <p className="muted">Расходов пока нет</p>}
      </section>
      <TransactionTable
        transactions={txs.data?.items ?? []}
        categories={categories.data ?? []}
        filters={filters}
        setFilters={setFilters}
        onDone={refresh}
        onError={(e) => setError(errorMessage(e))}
      />
    </main>
  );
}

function Metric({ label, value, tone }: { label: string; value: string; tone: string }) {
  return <article className={`metric ${tone}`}><span>{label}</span><strong>{value} ₽</strong></article>;
}

function TransactionForm({ categories, onDone, onError }: { categories: Category[]; onDone: () => void; onError: (e: unknown) => void }) {
  const [form, setForm] = useState({ amount: "", operation_type: "expense", category_id: "", occurred_at: today, comment: "" });
  const mutation = useMutation({ mutationFn: api.createTransaction, onSuccess: () => { setForm({ ...form, amount: "", comment: "" }); onDone(); }, onError });
  const filteredCategories = useMemo(() => categories.filter((c) => !c.operation_type_hint || c.operation_type_hint === form.operation_type), [categories, form.operation_type]);
  const categoryId = form.category_id || filteredCategories[0]?.id || "";
  return (
    <form className="panel" onSubmit={(e) => { e.preventDefault(); if (!Number(form.amount) || Number(form.amount) <= 0) return onError(new Error("Сумма должна быть больше 0")); mutation.mutate({ ...form, category_id: categoryId }); }}>
      <h2>Новая операция</h2>
      <div className="form-grid">
        <label>Сумма<input value={form.amount} type="number" step="0.01" min="0.01" onChange={(e) => setForm({ ...form, amount: e.target.value })} /></label>
        <label>Тип<select value={form.operation_type} onChange={(e) => setForm({ ...form, operation_type: e.target.value, category_id: "" })}><option value="expense">Расход</option><option value="income">Доход</option></select></label>
        <label>Категория<select value={categoryId} onChange={(e) => setForm({ ...form, category_id: e.target.value })}>{filteredCategories.map((c) => <option value={c.id} key={c.id}>{c.name}</option>)}</select></label>
        <label>Дата<input value={form.occurred_at} type="date" onChange={(e) => setForm({ ...form, occurred_at: e.target.value })} /></label>
      </div>
      <label>Комментарий<input value={form.comment} maxLength={500} onChange={(e) => setForm({ ...form, comment: e.target.value })} /></label>
      <button className="primary" disabled={mutation.isPending}>Добавить</button>
    </form>
  );
}

function TransactionTable(props: { transactions: Transaction[]; categories: Category[]; filters: Record<string, string>; setFilters: (f: Record<string, string>) => void; onDone: () => void; onError: (e: unknown) => void }) {
  const del = useMutation({ mutationFn: api.deleteTransaction, onSuccess: props.onDone, onError: props.onError });
  const f = props.filters;
  return (
    <section className="panel">
      <h2>Операции</h2>
      <div className="filters">
        <input type="date" value={f.date_from ?? ""} onChange={(e) => props.setFilters({ ...f, date_from: e.target.value })} />
        <input type="date" value={f.date_to ?? ""} onChange={(e) => props.setFilters({ ...f, date_to: e.target.value })} />
        <select value={f.operation_type ?? ""} onChange={(e) => props.setFilters({ ...f, operation_type: e.target.value })}><option value="">Все типы</option><option value="income">Доход</option><option value="expense">Расход</option></select>
        <select value={f.category_id ?? ""} onChange={(e) => props.setFilters({ ...f, category_id: e.target.value })}><option value="">Все категории</option>{props.categories.map((c) => <option value={c.id} key={c.id}>{c.name}</option>)}</select>
        <input placeholder="Поиск" value={f.search ?? ""} onChange={(e) => props.setFilters({ ...f, search: e.target.value })} />
      </div>
      <div className="table-wrap"><table><thead><tr><th>Дата</th><th>Тип</th><th>Сумма</th><th>Категория</th><th>Комментарий</th><th>Источник</th><th></th></tr></thead><tbody>
        {props.transactions.map((t) => <tr key={t.id}><td>{t.occurred_at}</td><td>{t.operation_type === "income" ? "Доход" : "Расход"}</td><td>{t.amount}</td><td>{t.category.name}</td><td>{t.comment}</td><td>{t.source}</td><td><button onClick={() => confirm("Удалить операцию?") && del.mutate(t.id)}>Удалить</button></td></tr>)}
      </tbody></table></div>
      {props.transactions.length === 0 && <p className="muted">Операций пока нет</p>}
    </section>
  );
}

function ImportPanel({ categories, onDone, onError }: { categories: Category[]; onDone: () => void; onError: (e: unknown) => void }) {
  const [mode, setMode] = useState<"text" | "csv" | "image">("text");
  const [text, setText] = useState("01.07.2026 Списание 349,90 RUB Перекрёсток\n01.07.2026 Зачисление 5000,00 RUB Перевод от Иван\n02.07.2026 Списание 220,00 RUB Метро");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const importMutation = useMutation({
    mutationFn: () => mode === "text" ? api.importText(text) : api.importFile(mode, file!),
    onSuccess: (data) => { setPreview(data); setSelected(new Set(data.candidates.filter((c) => c.duplicate_status !== "exact_duplicate").map((c) => c.id))); },
    onError
  });
  const confirmMutation = useMutation({ mutationFn: () => api.confirmImport(preview!.job.id, Array.from(selected)), onSuccess: () => { setPreview(null); onDone(); }, onError });
  return (
    <section className="panel">
      <h2>AI-импорт</h2>
      <div className="segmented"><button className={mode === "text" ? "active" : ""} onClick={() => setMode("text")}>Текст</button><button className={mode === "csv" ? "active" : ""} onClick={() => setMode("csv")}>CSV</button><button className={mode === "image" ? "active" : ""} onClick={() => setMode("image")}>Изображение</button></div>
      {mode === "text" ? <textarea value={text} onChange={(e) => setText(e.target.value)} /> : <input type="file" accept={mode === "csv" ? ".csv,text/csv" : ".png,.jpg,.jpeg,.webp"} onChange={(e) => setFile(e.target.files?.[0] ?? null)} />}
      <button className="primary" disabled={importMutation.isPending || (mode !== "text" && !file)} onClick={() => importMutation.mutate()}>Распознать</button>
      {preview && <CandidateReview candidates={preview.candidates} categories={categories} selected={selected} setSelected={setSelected} onError={onError} />}
      {preview && <div className="actions"><button className="primary" disabled={confirmMutation.isPending || selected.size === 0} onClick={() => confirmMutation.mutate()}>Подтвердить выбранные</button><button disabled={confirmMutation.isPending} onClick={() => { setSelected(new Set()); confirmMutation.mutate(); }}>Отклонить все</button><button onClick={() => setPreview(null)}>Новый импорт</button></div>}
    </section>
  );
}

function CandidateReview(props: { candidates: ImportCandidate[]; categories: Category[]; selected: Set<string>; setSelected: (s: Set<string>) => void; onError: (e: unknown) => void }) {
  const patch = useMutation({ mutationFn: ({ id, payload }: { id: string; payload: Record<string, string> }) => api.patchCandidate(id, payload), onError: props.onError });
  function toggle(id: string) {
    const next = new Set(props.selected);
    next.has(id) ? next.delete(id) : next.add(id);
    props.setSelected(next);
  }
  return <div className="table-wrap"><table><thead><tr><th></th><th>Сумма</th><th>Тип</th><th>Категория</th><th>Дата</th><th>Комментарий</th><th>Дубли</th></tr></thead><tbody>
    {props.candidates.map((c) => <tr key={c.id} className={c.duplicate_status !== "none" ? "warn-row" : ""}>
      <td><input type="checkbox" checked={props.selected.has(c.id)} onChange={() => toggle(c.id)} /></td>
      <td><input defaultValue={c.amount} onBlur={(e) => patch.mutate({ id: c.id, payload: candidatePayload(c, props.categories, { amount: e.target.value }) })} /></td>
      <td><select defaultValue={c.operation_type} onChange={(e) => patch.mutate({ id: c.id, payload: candidatePayload(c, props.categories, { operation_type: e.target.value }) })}><option value="expense">Расход</option><option value="income">Доход</option></select></td>
      <td><select defaultValue={c.category.id} onChange={(e) => patch.mutate({ id: c.id, payload: candidatePayload(c, props.categories, { category_id: e.target.value }) })}>{props.categories.map((cat) => <option key={cat.id} value={cat.id}>{cat.name}</option>)}</select></td>
      <td><input type="date" defaultValue={c.occurred_at} onBlur={(e) => patch.mutate({ id: c.id, payload: candidatePayload(c, props.categories, { occurred_at: e.target.value }) })} /></td>
      <td><input defaultValue={c.comment ?? ""} onBlur={(e) => patch.mutate({ id: c.id, payload: candidatePayload(c, props.categories, { comment: e.target.value }) })} /></td>
      <td><span className="badge">{c.duplicate_status}</span></td>
    </tr>)}
  </tbody></table></div>;
}

function candidatePayload(c: ImportCandidate, categories: Category[], patch: Record<string, string>) {
  return { amount: c.amount, operation_type: c.operation_type, category_id: c.category.id || categories[0]?.id, occurred_at: c.occurred_at, comment: c.comment ?? "", ...patch };
}

import { useMemo, useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ResponsiveContainer, Tooltip, PieChart, Pie, Cell } from "recharts";
import * as api from "../api";
import { errorMessage } from "../api/client";
import type { Category, ExpenseByCategory, ImportCandidate, ImportPreview, Transaction, User } from "../types/api";

const today = new Date().toISOString().slice(0, 10);
const currentMonth = today.slice(0, 7);

const COLORS = ['#999596', '#35c3a9', '#e0a72c', '#2d7dc4', '#9a3fcb', '#d13d62', '#74c943', '#d4ac46'];

type SortField = "occurred_at" | "operation_type" | "amount" | "category" | "comment" | "source";
type SortDirection = "asc" | "desc";

const SORT_LABELS: Record<SortField, string> = {
  occurred_at: "Дата",
  operation_type: "Тип",
  amount: "Сумма",
  category: "Категория",
  comment: "Комментарий",
  source: "Источник",
};

export function DashboardPage({ user, onUserChange, onLogout }: { user: User; onUserChange: (user: User) => void; onLogout: () => void }) {
  const qc = useQueryClient();
  const [error, setError] = useState("");
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [selectedExpenseMonth, setSelectedExpenseMonth] = useState(currentMonth);
  const [profileOpen, setProfileOpen] = useState(false);
  const categories = useQuery({ queryKey: ["categories"], queryFn: api.categories });
  const txs = useQuery({ queryKey: ["transactions", filters], queryFn: () => api.transactions(filters) });
  const summary = useQuery({ queryKey: ["summary"], queryFn: () => api.summary() });
  const monthlySummary = useQuery({
    queryKey: ["summary", "month", selectedExpenseMonth],
    queryFn: () => api.summary(monthRange(selectedExpenseMonth)),
  });
  const expenses = useQuery({ queryKey: ["expenses"], queryFn: () => api.expensesByCategory() });
  const monthlyExpenses = useQuery({
    queryKey: ["expenses", "month", selectedExpenseMonth],
    queryFn: () => api.expensesByCategory(monthRange(selectedExpenseMonth)),
  });
  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["transactions"] });
    qc.invalidateQueries({ queryKey: ["summary"] });
    qc.invalidateQueries({ queryKey: ["expenses"] });
  };

  const expenseData = expenses.data ?? [];
  const monthlyExpenseData = monthlyExpenses.data ?? [];
  const colorMap = useMemo(() => {
    const allTimeAmounts = new Map(expenseData.map((item) => [item.category_name, Number(item.amount)]));
    const sortedCategoryNames = [...new Set([...expenseData, ...monthlyExpenseData].map((item) => item.category_name))]
      .sort((a, b) => (allTimeAmounts.get(b) ?? 0) - (allTimeAmounts.get(a) ?? 0) || a.localeCompare(b, "ru"));
    const map: Record<string, string> = {};
    sortedCategoryNames.forEach((name, index) => {
      map[name] = COLORS[index % COLORS.length];
    });
    map["Продукты"] = '#74c943';
    map["Транспорт"] = '#9a3fcb';
    map["Здоровье"] = '#35c3a9';
    map["Кафе и рестораны"] = "#e7a53c";
    map["Переводы"] = '#2d7dc4';
    map["Развлечения"] = '#d13d62';
    map["Другое"] = '#999596';
    return map;
  }, [expenseData, monthlyExpenseData]);

  return (
    <main>
      <header className="topbar">
        <h1>Finance AI Agent</h1>
        <div>
          <span>{user.display_name || user.email}</span>
          <button onClick={() => setProfileOpen((open) => !open)}>{profileOpen ? "Закрыть личный кабинет" : "Личный кабинет"}</button>
          <button onClick={onLogout}>Выйти</button>
        </div>
      </header>
      {error && <div className="banner">{error}<button onClick={() => setError("")}>×</button></div>}
      {profileOpen && <ProfilePanel user={user} onUserChange={onUserChange} onError={(e) => setError(errorMessage(e))} />}

      <div className="dashboard-layout">
        <div className="left-column">
          <div className="balance-block">
            <Metric label="Баланс" value={summary.data?.balance ?? "0.00"} tone="neutral" />
          </div>
          <div className="income-expense-row">
            <Metric label="Доход" value={summary.data?.income_total ?? "0.00"} tone="good" />
            <Metric label="Расход" value={summary.data?.expense_total ?? "0.00"} tone="bad" />
          </div>
        </div>
        <div className="right-column">
          <ImportPanel categories={categories.data ?? []} onDone={refresh} onError={(e) => setError(errorMessage(e))} />
        </div>
      </div>

      <section className="panel expense-panel">
        <div className="expense-header">
          <h2>Расходы по категориям</h2>
          <label className="month-filter">Месяц
            <input type="month" value={selectedExpenseMonth} onChange={(e) => setSelectedExpenseMonth(e.target.value || currentMonth)} />
          </label>
        </div>
        <div className="expense-charts">
          <div className="expense-chart-section">
            <h3>За все время</h3>
            <ExpensePieChart data={expenseData} colorMap={colorMap} balance={summary.data?.balance ?? "0.00"} emptyMessage="Операций пока нет" />
          </div>
          <div className="expense-chart-section">
            <h3>За выбранный месяц</h3>
            <ExpensePieChart data={monthlyExpenseData} colorMap={colorMap} balance={monthlySummary.data?.balance ?? "0.00"} emptyMessage="Операций за месяц пока нет" />
          </div>
        </div>
        <ExpenseLegend colorMap={colorMap} />
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

function ProfilePanel({ user, onUserChange, onError }: { user: User; onUserChange: (user: User) => void; onError: (e: unknown) => void }) {
  const [form, setForm] = useState({
    display_name: user.display_name,
    username: user.username,
    email: user.email,
    current_password: "",
    new_password: "",
  });
  const [saved, setSaved] = useState(false);
  const mutation = useMutation({
    mutationFn: api.updateMe,
    onSuccess: (updatedUser) => {
      onUserChange(updatedUser);
      setForm({
        display_name: updatedUser.display_name,
        username: updatedUser.username,
        email: updatedUser.email,
        current_password: "",
        new_password: "",
      });
      setSaved(true);
    },
    onError,
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaved(false);
    mutation.mutate(form);
  }

  return (
    <form className="panel profile-panel" onSubmit={submit}>
      <div className="profile-panel-header">
        <div>
          <h2>Личный кабинет</h2>
          <p className="hint">Для изменения любых данных аккаунта нужно указать актуальный пароль.</p>
        </div>
        {saved && <span className="save-status">Сохранено</span>}
      </div>
      <div className="form-grid">
        <label>Имя<input value={form.display_name} minLength={2} maxLength={120} onChange={(e) => setForm({ ...form, display_name: e.target.value })} /></label>
        <label>Логин<input value={form.username} minLength={3} maxLength={32} pattern="[a-zA-Z0-9_]+" onChange={(e) => setForm({ ...form, username: e.target.value })} /></label>
        <label>Email<input value={form.email} type="email" onChange={(e) => setForm({ ...form, email: e.target.value })} /></label>
      </div>
      <div className="form-grid">
        <label>Текущий пароль<input value={form.current_password} type="password" required autoComplete="current-password" onChange={(e) => setForm({ ...form, current_password: e.target.value })} /></label>
        <label>Новый пароль<input value={form.new_password} type="password" minLength={8} maxLength={128} autoComplete="new-password" onChange={(e) => setForm({ ...form, new_password: e.target.value })} /></label>
      </div>
      <div className="actions">
        <button className="primary" disabled={mutation.isPending}>{mutation.isPending ? "Сохранение..." : "Сохранить профиль"}</button>
      </div>
    </form>
  );
}

function ExpensePieChart({ data, colorMap, balance, emptyMessage }: { data: ExpenseByCategory[]; colorMap: Record<string, string>; balance: string; emptyMessage: string }) {
  const chartData = data.map((item) => ({ ...item, amount: Number(item.amount) }));
  const balanceValue = Number(balance);
  const balanceTone = balanceValue > 0 ? "positive" : balanceValue < 0 ? "negative" : "neutral";
  const balanceText = formatMoneyWithSign(balanceValue);
  if (chartData.length === 0) {
    return (
      <div className="expense-chart-empty">
        <div className="chart-balance">
          <span>Баланс</span>
          <strong className={balanceTone}>{balanceText}</strong>
        </div>
        <p className="muted">{emptyMessage}</p>
      </div>
    );
  }
  return (
    <div className="expense-chart">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            dataKey="amount"
            nameKey="category_name"
            cx="50%"
            cy="46%"
            outerRadius={92}
            innerRadius={78}
            stroke="none"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={colorMap[entry.category_name] || "#8884d8"} />
            ))}
          </Pie>
          <Tooltip formatter={(value) => `${Number(value).toFixed(2)} ₽`} />
        </PieChart>
      </ResponsiveContainer>
      <div className="chart-balance">
        <span>Баланс</span>
        <strong className={balanceTone}>{balanceText}</strong>
      </div>
    </div>
  );
}

function formatMoneyWithSign(value: number) {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)} ₽`;
}

function ExpenseLegend({ colorMap }: { colorMap: Record<string, string> }) {
  const items = Object.entries(colorMap);
  if (items.length === 0) return null;
  return (
    <div className="expense-legend" aria-label="Соответствие цветов категориям">
      {items.map(([name, color]) => (
        <span className="expense-legend-item" key={name}>
          <span className="expense-legend-swatch" style={{ backgroundColor: color }} />
          {name}
        </span>
      ))}
    </div>
  );
}

function monthRange(month: string): Record<string, string> {
  const [year, monthNumber] = month.split("-").map(Number);
  if (!year || !monthNumber) return {};
  const lastDay = new Date(year, monthNumber, 0).getDate();
  return {
    date_from: `${month}-01`,
    date_to: `${month}-${String(lastDay).padStart(2, "0")}`,
  };
}

function TransactionForm({ categories, onDone, onError }: { categories: Category[]; onDone: () => void; onError: (e: unknown) => void }) {
  const [form, setForm] = useState({ amount: "", operation_type: "expense", category_id: "", occurred_at: today, comment: "" });
  const mutation = useMutation({ mutationFn: api.createTransaction, onSuccess: () => { setForm({ ...form, amount: "", comment: "" }); onDone(); }, onError });
  const filteredCategories = useMemo(() => categories.filter((c) => !c.operation_type_hint || c.operation_type_hint === form.operation_type), [categories, form.operation_type]);
  const categoryId = form.category_id || filteredCategories[0]?.id || "";
  return (
    <form className="panel transaction-form" onSubmit={(e) => { e.preventDefault(); if (!Number(form.amount) || Number(form.amount) <= 0) return onError(new Error("Сумма должна быть больше 0")); mutation.mutate({ ...form, category_id: categoryId }); }}>
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
  const [sortField, setSortField] = useState<SortField>("occurred_at");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const sortedTransactions = useMemo(() => {
    const direction = sortDirection === "asc" ? 1 : -1;
    return [...props.transactions].sort((a, b) => {
      const result = compareTransactions(a, b, sortField);
      if (result !== 0) return result * direction;
      return compareTransactions(a, b, "occurred_at") * -1 || a.id.localeCompare(b.id);
    });
  }, [props.transactions, sortDirection, sortField]);

  function changeSort(field: SortField) {
    if (field === sortField) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
      return;
    }
    setSortField(field);
    setSortDirection(field === "occurred_at" || field === "amount" ? "desc" : "asc");
  }

  function sortLabel(field: SortField) {
    if (field !== sortField) return SORT_LABELS[field];
    return `${SORT_LABELS[field]} ${sortDirection === "asc" ? "↑" : "↓"}`;
  }

  return (
    <section className="panel">
      <h2>История операций</h2>
      <div className="filters">
        <input type="date" value={f.date_from ?? ""} onChange={(e) => props.setFilters({ ...f, date_from: e.target.value })} />
        <input type="date" value={f.date_to ?? ""} onChange={(e) => props.setFilters({ ...f, date_to: e.target.value })} />
        <select value={f.operation_type ?? ""} onChange={(e) => props.setFilters({ ...f, operation_type: e.target.value })}><option value="">Все типы</option><option value="income">Доход</option><option value="expense">Расход</option></select>
        <select value={f.category_id ?? ""} onChange={(e) => props.setFilters({ ...f, category_id: e.target.value })}><option value="">Все категории</option>{props.categories.map((c) => <option value={c.id} key={c.id}>{c.name}</option>)}</select>
        <input placeholder="Поиск" value={f.search ?? ""} onChange={(e) => props.setFilters({ ...f, search: e.target.value })} />
      </div>
      <div className="table-wrap"><table><thead><tr>
        <th><button type="button" className="sort-header" onClick={() => changeSort("occurred_at")}>{sortLabel("occurred_at")}</button></th>
        <th><button type="button" className="sort-header" onClick={() => changeSort("operation_type")}>{sortLabel("operation_type")}</button></th>
        <th><button type="button" className="sort-header" onClick={() => changeSort("amount")}>{sortLabel("amount")}</button></th>
        <th><button type="button" className="sort-header" onClick={() => changeSort("category")}>{sortLabel("category")}</button></th>
        <th className="comment-cell"><button type="button" className="sort-header" onClick={() => changeSort("comment")}>{sortLabel("comment")}</button></th>
        <th><button type="button" className="sort-header" onClick={() => changeSort("source")}>{sortLabel("source")}</button></th>
        <th></th>
      </tr></thead><tbody>
        {sortedTransactions.map((t) => <tr key={t.id}><td>{t.occurred_at}</td><td>{t.operation_type === "income" ? "Доход" : "Расход"}</td><td>{t.amount}</td><td>{t.category.name}</td><td className="comment-cell">{t.comment}</td><td>{t.source}</td><td><button onClick={() => confirm("Удалить операцию?") && del.mutate(t.id)}>Удалить</button></td></tr>)}
      </tbody></table></div>
      {props.transactions.length === 0 && <p className="muted">Операций пока нет</p>}
    </section>
  );
}

function compareTransactions(a: Transaction, b: Transaction, field: SortField) {
  if (field === "amount") {
    return Number(a.amount) - Number(b.amount);
  }
  const left = transactionSortValue(a, field);
  const right = transactionSortValue(b, field);
  return left.localeCompare(right, "ru", { numeric: true, sensitivity: "base" });
}

function transactionSortValue(transaction: Transaction, field: SortField) {
  if (field === "category") return transaction.category.name;
  if (field === "comment") return transaction.comment ?? "";
  return transaction[field];
}

function ImportPanel({ categories, onDone, onError }: { categories: Category[]; onDone: () => void; onError: (e: unknown) => void }) {
  const [mode, setMode] = useState<"text" | "csv" | "image" | "manual">("text");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const importMutation = useMutation({
    mutationFn: () => mode === "text" ? api.importText(text) : api.importFile(mode, file!),
    onSuccess: (data) => { setPreview(data); setSelected(new Set(data.candidates.filter((c) => c.duplicate_status !== "exact_duplicate").map((c) => c.id))); },
    onError
  });

  const confirmMutation = useMutation({
    mutationFn: () => api.confirmImport(preview!.job.id, Array.from(selected)),
    onSuccess: () => { setPreview(null); onDone(); },
    onError
  });

  function handleModeChange(newMode: typeof mode) {
    setMode(newMode);
  }

  return (
    <section className={`panel import-panel ${preview ? "has-preview" : ""}`}>
      <h2>Новая операция с ИИ-агентом</h2>
      <div className="segmented">
        <button className={mode === "text" ? "active" : ""} onClick={() => handleModeChange("text")}>Текст</button>
        <button className={mode === "csv" ? "active" : ""} onClick={() => handleModeChange("csv")}>CSV</button>
        <button className={mode === "image" ? "active" : ""} onClick={() => handleModeChange("image")}>Изображение</button>
        <button className={mode === "manual" ? "active" : ""} onClick={() => handleModeChange("manual")}>Ручной ввод</button>
      </div>

      {mode === "manual" ? (
        <TransactionForm key="manual-form" categories={categories} onDone={onDone} onError={onError} />
      ) : (
        <>
          <div className="import-input-area">
            {mode === "text" ? (
              <textarea className="import-textarea" value={text} onChange={(e) => setText(e.target.value)} />
            ) : (
              <label className="file-dropzone">
                <input type="file" accept={mode === "csv" ? ".csv,text/csv" : ".png,.jpg,.jpeg,.webp"} onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
                <span className="file-dropzone-title">{mode === "csv" ? "Выберите CSV-файл" : "Выберите изображение"}</span>
                <span className="file-dropzone-text">{file ? file.name : "Нажмите сюда, чтобы выбрать файл"}</span>
              </label>
            )}
          </div>
          <button className="primary" disabled={importMutation.isPending || (mode !== "text" && !file)} onClick={() => importMutation.mutate()}>Распознать</button>
        </>
      )}

      {preview && (
        <>
          <CandidateReview candidates={preview.candidates} categories={categories} selected={selected} setSelected={setSelected} onError={onError} />
          <div className="actions">
            <button className="primary" disabled={confirmMutation.isPending || selected.size === 0} onClick={() => confirmMutation.mutate()}>Подтвердить выбранные</button>
            <button disabled={confirmMutation.isPending} onClick={() => { setSelected(new Set()); confirmMutation.mutate(); }}>Отклонить все</button>
            <button onClick={() => setPreview(null)}>Новый импорт</button>
          </div>
        </>
      )}
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
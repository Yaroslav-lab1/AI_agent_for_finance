export type User = { id: string; email: string; username: string; display_name: string };
export type Category = { id: string; slug: string; name: string; operation_type_hint: string | null };
export type Transaction = {
  id: string;
  amount: string;
  operation_type: "income" | "expense";
  category: Category;
  occurred_at: string;
  comment: string | null;
  source: string;
  created_at: string;
  updated_at: string;
};
export type Summary = { income_total: string; expense_total: string; balance: string };
export type ExpenseByCategory = { category_id: string; category_slug: string; category_name: string; amount: string };
export type ImportJob = { id: string; source_type: string; status: string; candidates_count: number; error_message?: string | null };
export type ImportCandidate = {
  id: string;
  amount: string;
  operation_type: "income" | "expense";
  category: Category;
  occurred_at: string;
  comment: string | null;
  confidence: string;
  duplicate_status: string;
  duplicate_transaction_id: string | null;
  status: string;
};
export type ImportPreview = { job: ImportJob; candidates: ImportCandidate[] };

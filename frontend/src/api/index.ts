import { api } from "./client";
import type { Category, ExpenseByCategory, ImportPreview, Summary, Transaction, User } from "../types/api";

export async function register(payload: { email: string; username: string; display_name: string; password: string }): Promise<User> {
  return (await api.post("/auth/register", payload)).data;
}

export async function login(email: string, password: string): Promise<string> {
  return (await api.post("/auth/login", { email, password })).data.access_token;
}

export async function me(): Promise<User> {
  return (await api.get("/auth/me")).data;
}

export async function categories(): Promise<Category[]> {
  return (await api.get("/categories")).data;
}

export async function transactions(params: Record<string, string>): Promise<{ items: Transaction[]; total: number }> {
  return (await api.get("/transactions", { params: compactParams(params) })).data;
}

export async function createTransaction(payload: Record<string, string>): Promise<Transaction> {
  return (await api.post("/transactions", payload)).data;
}

export async function updateTransaction(id: string, payload: Record<string, string>): Promise<Transaction> {
  return (await api.put(`/transactions/${id}`, payload)).data;
}

export async function deleteTransaction(id: string): Promise<void> {
  await api.delete(`/transactions/${id}`);
}

export async function summary(): Promise<Summary> {
  return (await api.get("/stats/summary")).data;
}

export async function expensesByCategory(): Promise<ExpenseByCategory[]> {
  return (await api.get("/stats/expenses-by-category")).data;
}

export async function importText(text: string): Promise<ImportPreview> {
  return (await api.post("/imports/text", { text })).data;
}

export async function importFile(path: "csv" | "image", file: File): Promise<ImportPreview> {
  const data = new FormData();
  data.append("file", file);
  return (await api.post(`/imports/${path}`, data)).data;
}

export async function patchCandidate(id: string, payload: Record<string, string>): Promise<void> {
  await api.patch(`/imports/candidates/${id}`, payload);
}

export async function confirmImport(jobId: string, candidateIds: string[]): Promise<void> {
  await api.post(`/imports/${jobId}/confirm`, { candidate_ids: candidateIds, reject_other_candidates: true });
}

function compactParams(params: Record<string, string>): Record<string, string> {
  return Object.fromEntries(Object.entries(params).filter(([, value]) => value.trim() !== ""));
}

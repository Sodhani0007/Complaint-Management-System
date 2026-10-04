import axios from "axios";
import type {
  ComplaintCreatePayload,
  ComplaintRead,
  CompletenessCheckResult,
  DuplicateCheckResult,
  ExtractionResponse,
  RiskAssessmentResult,
  SummaryResult,
} from "../types/complaint";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api/v1",
  timeout: 180000, // Allows a sleeping free-tier server to start; UI explains the wait.
});

let sessionToken: string | null = null;
export function setSessionToken(token: string | null) { sessionToken = token; }
client.interceptors.request.use((config) => {
  if (sessionToken) config.headers.Authorization = `Bearer ${sessionToken}`;
  return config;
});
client.interceptors.response.use((response) => response, (error) => {
  if (error.response?.status === 401 && sessionToken) {
    sessionToken = null;
    window.dispatchEvent(new Event("session-expired"));
  }
  return Promise.reject(error);
});

export interface Session { access_token: string; role: string; expires_in: number }
export async function getAuthConfig() {
  return (await client.get<{ demo_enabled: boolean; live_ai_enabled: boolean }>("/auth/config")).data;
}
export async function login(email: string, password: string) {
  return (await client.post<Session>("/auth/login", { email, password })).data;
}
export async function enterDemo() {
  return (await client.post<Session>("/auth/demo")).data;
}
export async function logout() { await client.post("/auth/logout"); }
export async function listComplaints() {
  return (await client.get<ComplaintRead[]>("/complaints", { params: { page_size: 20 } })).data;
}

export async function extractFromFile(file: File): Promise<ExtractionResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await client.post<ExtractionResponse>("/complaints/extract", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function extractFromText(text: string): Promise<ExtractionResponse> {
  const formData = new FormData();
  formData.append("text", text);
  const { data } = await client.post<ExtractionResponse>("/complaints/extract", formData);
  return data;
}

export async function saveComplaint(payload: ComplaintCreatePayload): Promise<ComplaintRead> {
  const { data } = await client.post<ComplaintRead>("/complaints", payload);
  return data;
}

export async function getComplaint(id: number): Promise<ComplaintRead> {
  const { data } = await client.get<ComplaintRead>(`/complaints/${id}`);
  return data;
}

// --- Bonus AI features — all operate on an already-saved complaint ---

export async function checkCompleteness(complaintId: number): Promise<CompletenessCheckResult> {
  const { data } = await client.post<CompletenessCheckResult>(`/complaints/${complaintId}/completeness-check`);
  return data;
}

export async function generateSummary(complaintId: number): Promise<SummaryResult> {
  const { data } = await client.post<SummaryResult>(`/complaints/${complaintId}/summary`);
  return data;
}

export async function checkDuplicates(complaintId: number): Promise<DuplicateCheckResult> {
  const { data } = await client.post<DuplicateCheckResult>(`/complaints/${complaintId}/duplicate-check`);
  return data;
}

export async function getRiskAssessment(complaintId: number): Promise<RiskAssessmentResult> {
  const { data } = await client.post<RiskAssessmentResult>(`/complaints/${complaintId}/risk-assessment`);
  return data;
}

/** Normalizes axios errors into a plain message string — components and
 * Redux slices should never need to know axios's error shape directly. */
export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((item) => `${item.loc?.slice(1).join(".")}: ${item.msg}`).join("; ");
    return error.message || "Request failed";
  }
  return error instanceof Error ? error.message : "Unknown error";
}

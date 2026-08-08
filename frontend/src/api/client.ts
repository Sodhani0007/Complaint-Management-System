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
  baseURL: "/api/v1",
  timeout: 45000, // extraction can take a few seconds through the LangGraph retry loop
});

export async function extractFromFile(file: File): Promise<ExtractionResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await client.post<ExtractionResponse>("/complaints/extract", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function extractFromText(text: string): Promise<ExtractionResponse> {
  const { data } = await client.post<ExtractionResponse>("/complaints/extract", null, {
    params: { text },
  });
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
    return error.response?.data?.detail ?? error.message ?? "Request failed";
  }
  return error instanceof Error ? error.message : "Unknown error";
}

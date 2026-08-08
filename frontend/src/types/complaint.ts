/**
 * Mirrors app/schemas/extraction.py and app/schemas/complaint.py on the
 * backend. Kept as a single source of truth here so every component and
 * slice imports the same shape rather than each inventing its own — the
 * classic frontend/backend drift bug this avoids is a field renamed on one
 * side and silently ignored on the other.
 */

export type Severity = "Critical" | "Major" | "Minor";
export type Priority = "High" | "Medium" | "Low";
export type ComplaintStatus = "Pending Triage" | "Under Investigation" | "Closed";

export interface ExtractedFields {
  complaint_source: string | null;
  customer_name: string | null;
  product_name: string | null;
  product_strength_grade: string | null;
  batch_lot_number: string | null;
  manufacturing_date: string | null;
  expiry_date: string | null;
  quantity_affected: number | null;
  complaint_type: string | null;
  complaint_date: string | null;
  description: string | null;
  initial_severity: Severity | null;
  priority: Priority | null;
}

export interface ExtractionResponse {
  extraction_id: string;
  fields: ExtractedFields;
  confidence_score: number;
  model_used: string;
  missing_required_fields: string[];
}

export interface ComplaintCreatePayload {
  product_name: string;
  batch_lot_number: string;
  description: string;
  complaint_source?: string | null;
  customer_name?: string | null;
  complaint_type?: string | null;
  complaint_date?: string | null;
  manufacturing_date?: string | null;
  expiry_date?: string | null;
  quantity_affected?: number | null;
  severity?: Severity | null;
  priority?: Priority | null;
  ai_extraction_snapshot?: Record<string, unknown> | null;
  ai_model_used?: string | null;
  ai_confidence?: number | null;
}

export interface ComplaintRead extends ComplaintCreatePayload {
  id: number;
  batch_id: number | null;
  product_id: number | null;
  status: ComplaintStatus;
  created_at: string;
  updated_at: string;
}

/** Bonus AI feature response shapes — mirror app/schemas/bonus_features.py exactly. */

export interface CompletenessCheckResult {
  is_complete: boolean;
  missing_fields: string[];
  warnings: string[];
  suggested_next_action: string;
  confidence: number;
}

export interface SummaryResult {
  summary: string;
  product: string | null;
  batch: string | null;
  customer: string | null;
  issue: string | null;
  severity: string | null;
  potential_impact: string;
  recommended_next_step: string;
  confidence: number;
}

export interface DuplicateMatch {
  matched_complaint_id: number;
  similarity_score: number;
  reason: string;
}

export interface DuplicateCheckResult {
  is_duplicate: boolean;
  matches: DuplicateMatch[];
}

export interface RiskAssessmentResult {
  severity: string;
  priority: string;
  confidence: number;
  reasoning: string;
  recommended_escalation: string;
  business_rule_applied: boolean;
}

/** Empty-state factory — used both to initialize the Redux slice and to
 * reset the form, so there's exactly one definition of "what a blank
 * complaint looks like" instead of duplicated object literals. */
export function emptyComplaintFields(): ExtractedFields {
  return {
    complaint_source: null,
    customer_name: null,
    product_name: null,
    product_strength_grade: null,
    batch_lot_number: null,
    manufacturing_date: null,
    expiry_date: null,
    quantity_affected: null,
    complaint_type: null,
    complaint_date: null,
    description: null,
    initial_severity: null,
    priority: null,
  };
}

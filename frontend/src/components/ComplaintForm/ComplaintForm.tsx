import { useAppDispatch, useAppSelector } from "../../hooks/reduxHooks";
import { resetExtraction } from "../../store/slices/extractionSlice";
import { resetForm, submitComplaint, updateField } from "../../store/slices/complaintSlice";
import { Badge, toneFromSeverity } from "../common/Badge";
import { Button } from "../common/Button";
import { Card } from "../common/Card";
import type { ExtractedFields } from "../../types/complaint";
import { AssessmentPrioritySection, ComplaintDetailsSection, OriginCustomerSection, ProductBatchSection } from "./FormSections";
import { InsightsPanel } from "./InsightsPanel";

export function ComplaintForm() {
  const dispatch = useAppDispatch();
  const { fields, saveStatus, errorMessage, savedComplaint } = useAppSelector((s) => s.complaint);
  const { extractionId, confidenceScore, modelUsed } = useAppSelector((s) => s.extraction);

  const handleFieldChange = (field: keyof ExtractedFields, value: string) => {
    const isNumeric = field === "quantity_affected";
    dispatch(updateField({ field, value: isNumeric ? (value === "" ? null : Number(value)) : value }));
  };

  const handleSave = () => {
    dispatch(
      submitComplaint({
        extractionSnapshot: extractionId ? (fields as unknown as Record<string, unknown>) : null,
        modelUsed,
        confidence: confidenceScore,
      })
    );
  };

  const handleReset = () => {
    dispatch(resetForm());
    dispatch(resetExtraction());
  };

  return (
    <>
      <Card>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px" }}>
          <div>
            <h1 style={{ fontSize: "20px", fontWeight: 700, margin: 0 }}>Log Customer Complaint</h1>
            <p style={{ fontSize: "13px", color: "var(--color-text-secondary)", margin: "4px 0 0" }}>
              API &amp; FDF Quality Assurance Module
            </p>
          </div>
          <Badge label={savedComplaint ? savedComplaint.status : "Pending Triage"} tone="major" />
        </div>

        <OriginCustomerSection fields={fields} onFieldChange={handleFieldChange} />
        <ProductBatchSection fields={fields} onFieldChange={handleFieldChange} />
        <ComplaintDetailsSection fields={fields} onFieldChange={handleFieldChange} />
        <AssessmentPrioritySection fields={fields} onFieldChange={handleFieldChange} />

        {fields.initial_severity && (
          <div style={{ marginTop: "16px" }}>
            <Badge label={`Severity: ${fields.initial_severity}`} tone={toneFromSeverity(fields.initial_severity)} />
          </div>
        )}

        {errorMessage && (
          <div
            style={{
              marginTop: "16px",
              padding: "12px",
              background: "var(--color-critical-bg)",
              color: "var(--color-critical)",
              borderRadius: "var(--radius-sm)",
              fontSize: "13px",
            }}
          >
            {errorMessage}
          </div>
        )}

        {saveStatus === "saved" && savedComplaint && (
          <div
            style={{
              marginTop: "16px",
              padding: "12px",
              background: "var(--color-success-bg)",
              color: "var(--color-success)",
              borderRadius: "var(--radius-sm)",
              fontSize: "13px",
            }}
          >
            Complaint #{savedComplaint.id} saved successfully.
          </div>
        )}

        <div style={{ display: "flex", justifyContent: "space-between", marginTop: "24px" }}>
          <Button variant="secondary" onClick={handleReset}>
            ↺ Reset Form
          </Button>
          <Button onClick={handleSave} disabled={saveStatus === "saving"}>
            {saveStatus === "saving" ? "Saving..." : "💾 Save Complaint"}
          </Button>
        </div>
      </Card>

      {/* Bonus AI features only make sense once a complaint actually has an
          ID to operate on — shown as a separate card below the form rather
          than crammed inside it, so the save flow stays visually primary. */}
      {saveStatus === "saved" && savedComplaint && <InsightsPanel complaintId={savedComplaint.id} />}
    </>
  );
}

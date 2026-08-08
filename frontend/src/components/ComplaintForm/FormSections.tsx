/**
 * The four sections mirror the reference UI's numbered layout exactly:
 * 1. Origin & Customer Details, 2. Product & Batch Identification,
 * 3. Complaint Details, 4. Initial Assessment & Priority.
 * Each takes `fields` + `onFieldChange` rather than reading Redux directly —
 * keeps these components presentational/testable without a store in tests.
 */

import { FormField } from "../common/FormField";
import type { ExtractedFields } from "../../types/complaint";

interface SectionProps {
  fields: ExtractedFields;
  onFieldChange: (field: keyof ExtractedFields, value: string) => void;
}

function SectionHeading({ number, title }: { number: number; title: string }) {
  return (
    <div
      style={{
        fontSize: "12px",
        fontWeight: 600,
        letterSpacing: "0.04em",
        color: "var(--color-text-secondary)",
        textTransform: "uppercase",
        marginBottom: "14px",
        paddingBottom: "10px",
        borderBottom: "1px solid var(--color-border)",
      }}
    >
      {number}. {title}
    </div>
  );
}

const twoColStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "1fr 1fr",
  gap: "16px",
};

export function OriginCustomerSection({ fields, onFieldChange }: SectionProps) {
  return (
    <section style={{ marginBottom: "24px" }}>
      <SectionHeading number={1} title="Origin & Customer Details" />
      <div style={twoColStyle}>
        <FormField label="Complaint Source" value={fields.complaint_source} onChange={(v) => onFieldChange("complaint_source", v)} />
        <FormField label="Customer Name" value={fields.customer_name} onChange={(v) => onFieldChange("customer_name", v)} />
      </div>
    </section>
  );
}

export function ProductBatchSection({ fields, onFieldChange }: SectionProps) {
  return (
    <section style={{ marginBottom: "24px" }}>
      <SectionHeading number={2} title="Product & Batch Identification" />
      <div style={twoColStyle}>
        <FormField label="Product Name" value={fields.product_name} onChange={(v) => onFieldChange("product_name", v)} />
        <FormField label="Product Strength/Grade" value={fields.product_strength_grade} onChange={(v) => onFieldChange("product_strength_grade", v)} />
        <FormField label="Batch/Lot Number" value={fields.batch_lot_number} onChange={(v) => onFieldChange("batch_lot_number", v)} />
        <FormField label="Manufacturing Date" type="date" value={fields.manufacturing_date} onChange={(v) => onFieldChange("manufacturing_date", v)} />
        <FormField label="Expiry Date" type="date" value={fields.expiry_date} onChange={(v) => onFieldChange("expiry_date", v)} />
        <FormField label="Quantity Affected" type="number" unit="kg" value={fields.quantity_affected} onChange={(v) => onFieldChange("quantity_affected", v)} />
      </div>
    </section>
  );
}

export function ComplaintDetailsSection({ fields, onFieldChange }: SectionProps) {
  return (
    <section style={{ marginBottom: "24px" }}>
      <SectionHeading number={3} title="Complaint Details" />
      <div style={twoColStyle}>
        <FormField label="Complaint Type" value={fields.complaint_type} onChange={(v) => onFieldChange("complaint_type", v)} />
        <FormField label="Complaint Date" type="date" value={fields.complaint_date} onChange={(v) => onFieldChange("complaint_date", v)} />
      </div>
      <FormField label="Detailed Complaint Description" type="textarea" value={fields.description} onChange={(v) => onFieldChange("description", v)} />
    </section>
  );
}

export function AssessmentPrioritySection({ fields, onFieldChange }: SectionProps) {
  return (
    <section>
      <SectionHeading number={4} title="Initial Assessment & Priority" />
      <div style={twoColStyle}>
        <FormField
          label="Initial Severity"
          type="select"
          options={["Critical", "Major", "Minor"]}
          value={fields.initial_severity}
          onChange={(v) => onFieldChange("initial_severity", v)}
        />
        <FormField
          label="Priority"
          type="select"
          options={["High", "Medium", "Low"]}
          value={fields.priority}
          onChange={(v) => onFieldChange("priority", v)}
        />
      </div>
    </section>
  );
}

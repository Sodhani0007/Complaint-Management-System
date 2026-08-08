/**
 * On-demand AI insights for an already-saved complaint: Completeness Check,
 * Summary, and Duplicate Detection. Deliberately local useState rather than
 * a new Redux slice — nothing else in the app needs this data, and routing
 * every on-demand, single-component fetch through global state would be
 * unjustified complexity for what's essentially three independent buttons.
 *
 * Each section is expand/collapse and independently loadable, per the
 * "expand/collapse sections" + "clear AI labeling" UX requirement — no
 * section blocks the others, and nothing here is auto-triggered on save,
 * since these are optional QA-analyst-initiated actions, not part of the
 * required intake flow.
 */

import { useState } from "react";
import { checkCompleteness, checkDuplicates, extractErrorMessage, generateSummary, getRiskAssessment } from "../../api/client";
import type { CompletenessCheckResult, DuplicateCheckResult, RiskAssessmentResult, SummaryResult } from "../../types/complaint";
import { Badge, toneFromSeverity } from "../common/Badge";
import { Card } from "../common/Card";

type SectionStatus = "idle" | "loading" | "done" | "error";

interface InsightsPanelProps {
  complaintId: number;
}

function ConfidenceBadge({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const tone = confidence >= 0.7 ? "success" : confidence >= 0.4 ? "major" : "critical";
  return <Badge label={`${pct}% confidence`} tone={tone} />;
}

function SectionHeader({
  icon,
  title,
  isOpen,
  onToggle,
}: {
  icon: string;
  title: string;
  isOpen: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      onClick={onToggle}
      style={{
        width: "100%",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "12px 0",
        background: "none",
        border: "none",
        borderBottom: "1px solid var(--color-border)",
        cursor: "pointer",
        fontSize: "14px",
        fontWeight: 600,
        textAlign: "left",
      }}
    >
      <span>
        {icon} {title}
      </span>
      <span style={{ color: "var(--color-text-secondary)" }}>{isOpen ? "−" : "+"}</span>
    </button>
  );
}

export function InsightsPanel({ complaintId }: InsightsPanelProps) {
  const [openSection, setOpenSection] = useState<"completeness" | "summary" | "duplicates" | "risk" | null>(null);

  const [completenessStatus, setCompletenessStatus] = useState<SectionStatus>("idle");
  const [completenessResult, setCompletenessResult] = useState<CompletenessCheckResult | null>(null);
  const [completenessError, setCompletenessError] = useState<string | null>(null);

  const [summaryStatus, setSummaryStatus] = useState<SectionStatus>("idle");
  const [summaryResult, setSummaryResult] = useState<SummaryResult | null>(null);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  const [duplicateStatus, setDuplicateStatus] = useState<SectionStatus>("idle");
  const [duplicateResult, setDuplicateResult] = useState<DuplicateCheckResult | null>(null);
  const [duplicateError, setDuplicateError] = useState<string | null>(null);

  const [riskStatus, setRiskStatus] = useState<SectionStatus>("idle");
  const [riskResult, setRiskResult] = useState<RiskAssessmentResult | null>(null);
  const [riskError, setRiskError] = useState<string | null>(null);

  const toggle = (section: "completeness" | "summary" | "duplicates" | "risk") => {
    setOpenSection(openSection === section ? null : section);
  };

  const runCompleteness = async () => {
    setCompletenessStatus("loading");
    setCompletenessError(null);
    try {
      setCompletenessResult(await checkCompleteness(complaintId));
      setCompletenessStatus("done");
    } catch (err) {
      setCompletenessError(extractErrorMessage(err));
      setCompletenessStatus("error");
    }
  };

  const runSummary = async () => {
    setSummaryStatus("loading");
    setSummaryError(null);
    try {
      setSummaryResult(await generateSummary(complaintId));
      setSummaryStatus("done");
    } catch (err) {
      setSummaryError(extractErrorMessage(err));
      setSummaryStatus("error");
    }
  };

  const runDuplicates = async () => {
    setDuplicateStatus("loading");
    setDuplicateError(null);
    try {
      setDuplicateResult(await checkDuplicates(complaintId));
      setDuplicateStatus("done");
    } catch (err) {
      setDuplicateError(extractErrorMessage(err));
      setDuplicateStatus("error");
    }
  };

  const runRiskAssessment = async () => {
    setRiskStatus("loading");
    setRiskError(null);
    try {
      setRiskResult(await getRiskAssessment(complaintId));
      setRiskStatus("done");
    } catch (err) {
      setRiskError(extractErrorMessage(err));
      setRiskStatus("error");
    }
  };

  return (
    <Card style={{ marginTop: "16px" }}>
      <h3 style={{ fontSize: "14px", fontWeight: 700, margin: "0 0 4px" }}>AI Insights</h3>
      <p style={{ fontSize: "12px", color: "var(--color-text-secondary)", margin: "0 0 8px" }}>
        Optional, on-demand — AI-generated, human review recommended before acting.
      </p>

      {/* Completeness Checker */}
      <SectionHeader
        icon="✅"
        title="Completeness Checker"
        isOpen={openSection === "completeness"}
        onToggle={() => toggle("completeness")}
      />
      {openSection === "completeness" && (
        <div style={{ padding: "12px 0" }}>
          {completenessStatus === "idle" && (
            <button onClick={runCompleteness} style={linkButtonStyle}>
              Run completeness check
            </button>
          )}
          {completenessStatus === "loading" && <Skeleton />}
          {completenessStatus === "error" && <ErrorText message={completenessError} onRetry={runCompleteness} />}
          {completenessStatus === "done" && completenessResult && (
            <div style={{ fontSize: "13px" }}>
              <Badge
                label={completenessResult.is_complete ? "Complete" : "Incomplete"}
                tone={completenessResult.is_complete ? "success" : "major"}
              />
              {completenessResult.missing_fields.length > 0 && (
                <p style={{ marginTop: "8px" }}>
                  <strong>Missing:</strong> {completenessResult.missing_fields.join(", ")}
                </p>
              )}
              {completenessResult.warnings.length > 0 && (
                <p style={{ marginTop: "8px" }}>
                  <strong>Warnings:</strong> {completenessResult.warnings.join("; ")}
                </p>
              )}
              <p style={{ marginTop: "8px", color: "var(--color-text-secondary)" }}>
                {completenessResult.suggested_next_action}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Complaint Summary */}
      <SectionHeader
        icon="📝"
        title="Complaint Summary"
        isOpen={openSection === "summary"}
        onToggle={() => toggle("summary")}
      />
      {openSection === "summary" && (
        <div style={{ padding: "12px 0" }}>
          {summaryStatus === "idle" && (
            <button onClick={runSummary} style={linkButtonStyle}>
              Generate summary
            </button>
          )}
          {summaryStatus === "loading" && <Skeleton />}
          {summaryStatus === "error" && <ErrorText message={summaryError} onRetry={runSummary} />}
          {summaryStatus === "done" && summaryResult && (
            <div style={{ fontSize: "13px" }}>
              {summaryResult.summary === "insufficient_information" ? (
                <p style={{ color: "var(--color-text-secondary)" }}>
                  Not enough information to generate a reliable summary yet.
                </p>
              ) : (
                <>
                  <p>{summaryResult.summary}</p>
                  <p style={{ marginTop: "8px" }}>
                    <strong>Potential impact:</strong> {summaryResult.potential_impact}
                  </p>
                  <p style={{ marginTop: "4px" }}>
                    <strong>Recommended next step:</strong> {summaryResult.recommended_next_step}
                  </p>
                  <div style={{ marginTop: "8px" }}>
                    <ConfidenceBadge confidence={summaryResult.confidence} />
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      )}

      {/* Duplicate Detection */}
      <SectionHeader
        icon="🔍"
        title="Duplicate Detection"
        isOpen={openSection === "duplicates"}
        onToggle={() => toggle("duplicates")}
      />
      {openSection === "duplicates" && (
        <div style={{ padding: "12px 0" }}>
          {duplicateStatus === "idle" && (
            <button onClick={runDuplicates} style={linkButtonStyle}>
              Check for duplicates
            </button>
          )}
          {duplicateStatus === "loading" && <Skeleton />}
          {duplicateStatus === "error" && <ErrorText message={duplicateError} onRetry={runDuplicates} />}
          {duplicateStatus === "done" && duplicateResult && (
            <div style={{ fontSize: "13px" }}>
              {!duplicateResult.is_duplicate ? (
                <Badge label="No likely duplicates found" tone="success" />
              ) : (
                <>
                  <Badge label={`${duplicateResult.matches.length} possible match(es)`} tone="major" />
                  {duplicateResult.matches.map((m) => (
                    <div
                      key={m.matched_complaint_id}
                      style={{
                        marginTop: "8px",
                        padding: "8px",
                        background: "var(--color-bg)",
                        borderRadius: "var(--radius-sm)",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span>Complaint #{m.matched_complaint_id}</span>
                        <span>{Math.round(m.similarity_score * 100)}% similar</span>
                      </div>
                      <p style={{ margin: "4px 0 0", color: "var(--color-text-secondary)" }}>{m.reason}</p>
                    </div>
                  ))}
                </>
              )}
            </div>
          )}
        </div>
      )}

      {/* Risk Assessment (re-assessment against current saved data) */}
      <SectionHeader
        icon="⚠️"
        title="Risk Assessment"
        isOpen={openSection === "risk"}
        onToggle={() => toggle("risk")}
      />
      {openSection === "risk" && (
        <div style={{ padding: "12px 0" }}>
          {riskStatus === "idle" && (
            <button onClick={runRiskAssessment} style={linkButtonStyle}>
              Re-run risk assessment
            </button>
          )}
          {riskStatus === "loading" && <Skeleton />}
          {riskStatus === "error" && <ErrorText message={riskError} onRetry={runRiskAssessment} />}
          {riskStatus === "done" && riskResult && (
            <div style={{ fontSize: "13px" }}>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                <Badge label={`Severity: ${riskResult.severity}`} tone={toneFromSeverity(riskResult.severity)} />
                <Badge label={`Priority: ${riskResult.priority}`} tone="neutral" />
                <ConfidenceBadge confidence={riskResult.confidence} />
              </div>
              <p style={{ marginTop: "8px" }}>{riskResult.reasoning}</p>
              {riskResult.business_rule_applied && (
                <p style={{ marginTop: "6px", color: "var(--color-critical)", fontWeight: 600 }}>
                  ⚠ Escalated by deterministic safety-keyword rule, not AI judgment alone.
                </p>
              )}
              <p style={{ marginTop: "8px", color: "var(--color-text-secondary)" }}>
                {riskResult.recommended_escalation}
              </p>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

function Skeleton() {
  return (
    <div
      style={{
        height: "14px",
        borderRadius: "4px",
        background:
          "linear-gradient(90deg, var(--color-border) 25%, var(--color-bg) 50%, var(--color-border) 75%)",
        backgroundSize: "200% 100%",
        animation: "skeleton-pulse 1.4s ease-in-out infinite",
      }}
    >
      <style>{`@keyframes skeleton-pulse { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }`}</style>
    </div>
  );
}

function ErrorText({ message, onRetry }: { message: string | null; onRetry: () => void }) {
  return (
    <div style={{ fontSize: "13px", color: "var(--color-critical)" }}>
      {message ?? "Something went wrong."}{" "}
      <button onClick={onRetry} style={{ ...linkButtonStyle, display: "inline" }}>
        Retry
      </button>
    </div>
  );
}

const linkButtonStyle: React.CSSProperties = {
  background: "none",
  border: "none",
  color: "var(--color-accent)",
  fontSize: "13px",
  fontWeight: 600,
  cursor: "pointer",
  padding: 0,
};

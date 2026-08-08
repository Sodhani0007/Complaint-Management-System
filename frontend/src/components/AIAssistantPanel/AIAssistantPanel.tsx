import { useState } from "react";
import { useAppDispatch, useAppSelector } from "../../hooks/reduxHooks";
import { runFileExtraction, runTextExtraction } from "../../store/slices/extractionSlice";
import { populateFromExtraction } from "../../store/slices/complaintSlice";
import { Badge } from "../common/Badge";
import { Card } from "../common/Card";
import { ExtractionProgress } from "./ExtractionProgress";
import { FileDropzone } from "./FileDropzone";

export function AIAssistantPanel() {
  const dispatch = useAppDispatch();
  const { status, confidenceScore, missingRequiredFields, errorMessage } = useAppSelector((s) => s.extraction);
  const [pastedText, setPastedText] = useState("");
  const [showPasteBox, setShowPasteBox] = useState(false);

  const isExtracting = status === "extracting";

  const handleFile = async (file: File) => {
    const result = await dispatch(runFileExtraction(file));
    if (runFileExtraction.fulfilled.match(result)) {
      dispatch(populateFromExtraction(result.payload.fields));
    }
  };

  const handlePasteSubmit = async () => {
    if (!pastedText.trim()) return;
    const result = await dispatch(runTextExtraction(pastedText));
    if (runTextExtraction.fulfilled.match(result)) {
      dispatch(populateFromExtraction(result.payload.fields));
    }
  };

  return (
    <Card>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <h2 style={{ fontSize: "16px", fontWeight: 700, margin: 0, display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ color: "var(--color-accent)" }}>✨</span> AI Complaint Intake Assistant
        </h2>
        <Badge label="BETA" tone="accent" />
      </div>

      <FileDropzone onFileSelected={handleFile} disabled={isExtracting} />

      <div style={{ display: "flex", alignItems: "center", gap: "12px", margin: "16px 0" }}>
        <div style={{ flex: 1, height: "1px", background: "var(--color-border)" }} />
        <span style={{ fontSize: "12px", color: "var(--color-text-secondary)" }}>OR</span>
        <div style={{ flex: 1, height: "1px", background: "var(--color-border)" }} />
      </div>

      {!showPasteBox && (
        <button
          onClick={() => setShowPasteBox(true)}
          disabled={isExtracting}
          style={{
            width: "100%",
            padding: "12px",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-sm)",
            background: "var(--color-surface)",
            fontSize: "14px",
            cursor: isExtracting ? "not-allowed" : "pointer",
            textAlign: "left",
          }}
        >
          📄 Paste Complaint Text / Email
        </button>
      )}

      {showPasteBox && (
        <div>
          <textarea
            value={pastedText}
            onChange={(e) => setPastedText(e.target.value)}
            placeholder="Paste the complaint email or text here..."
            rows={5}
            disabled={isExtracting}
            style={{
              width: "100%",
              padding: "10px 12px",
              fontSize: "14px",
              fontFamily: "var(--font-sans)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-sm)",
              resize: "vertical",
            }}
          />
          <button
            onClick={handlePasteSubmit}
            disabled={isExtracting || !pastedText.trim()}
            style={{
              marginTop: "8px",
              padding: "8px 16px",
              fontSize: "13px",
              fontWeight: 600,
              border: "none",
              borderRadius: "var(--radius-sm)",
              background: "var(--color-accent)",
              color: "#fff",
              cursor: isExtracting ? "not-allowed" : "pointer",
              opacity: isExtracting || !pastedText.trim() ? 0.6 : 1,
            }}
          >
            Extract from text
          </button>
        </div>
      )}

      {isExtracting && <ExtractionProgress statusText="Analyzing document content and extracting key details..." />}

      {status === "error" && (
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
          Couldn't process that document — {errorMessage}. Try a different file or paste the text instead.
        </div>
      )}

      <div
        style={{
          marginTop: "20px",
          padding: "14px",
          background: "var(--color-accent-bg)",
          borderRadius: "var(--radius-md)",
          fontSize: "13px",
          lineHeight: 1.5,
        }}
      >
        <span style={{ marginRight: "6px" }}>🤖</span>
        {status === "idle" &&
          "Upload a complaint document or paste text above. I will automatically extract the details and populate the form for you."}
        {status === "done" && confidenceScore !== null && (
          <>
            Extraction complete with {Math.round(confidenceScore * 100)}% confidence.
            {missingRequiredFields.length > 0 && (
              <> A few required fields ({missingRequiredFields.join(", ")}) need your review — please fill them in below.</>
            )}
            {missingRequiredFields.length === 0 && <> Please review the populated fields before saving.</>}
          </>
        )}
        {isExtracting && "Reading the document now — this usually takes a few seconds."}
      </div>

      <p style={{ fontSize: "11px", color: "var(--color-text-secondary)", marginTop: "12px", textAlign: "center" }}>
        AI responses may contain errors. Please verify information.
      </p>
    </Card>
  );
}

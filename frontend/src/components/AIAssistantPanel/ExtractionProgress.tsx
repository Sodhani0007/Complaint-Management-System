/**
 * The single most important microinteraction in the whole UI (per the
 * architecture doc's Step 13 note) — this is what makes the extraction feel
 * alive instead of like a frozen loading spinner. Progress is indeterminate
 * (we don't get real progress events from the backend), so it's animated
 * via CSS rather than driven by fake percentages that would lie to the user.
 */

interface ExtractionProgressProps {
  statusText: string;
}

export function ExtractionProgress({ statusText }: ExtractionProgressProps) {
  return (
    <div style={{ marginTop: "16px" }}>
      <style>{`
        @keyframes indeterminate-bar {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(250%); }
        }
      `}</style>
      <div
        style={{
          fontSize: "12px",
          fontWeight: 600,
          color: "var(--color-text-secondary)",
          textTransform: "uppercase",
          letterSpacing: "0.03em",
          marginBottom: "8px",
        }}
      >
        Extraction Progress
      </div>
      <div
        style={{
          height: "6px",
          borderRadius: "999px",
          background: "var(--color-border)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: "40%",
            borderRadius: "999px",
            background: "var(--color-accent)",
            animation: "indeterminate-bar 1.2s ease-in-out infinite",
          }}
        />
      </div>
      <p style={{ fontSize: "13px", color: "var(--color-text-secondary)", marginTop: "8px" }}>{statusText}</p>
    </div>
  );
}

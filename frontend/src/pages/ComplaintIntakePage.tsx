import { ComplaintForm } from "../components/ComplaintForm/ComplaintForm";
import { AIAssistantPanel } from "../components/AIAssistantPanel/AIAssistantPanel";

export function ComplaintIntakePage() {
  return (
    <div style={{ maxWidth: "1280px", margin: "0 auto", padding: "32px 24px" }}>
      <div
        className="two-pane-grid"
        style={{
          display: "grid",
          gridTemplateColumns: "1.3fr 1fr",
          gap: "24px",
          alignItems: "start",
        }}
      >
        <ComplaintForm />
        <AIAssistantPanel />
      </div>

      {/* Responsive collapse to single column under ~768px, per Step 6 of the
          architecture doc. Kept as a plain <style> tag rather than a CSS
          module since this is the only page in the app. */}
      <style>{`
        @media (max-width: 768px) {
          .two-pane-grid {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  );
}

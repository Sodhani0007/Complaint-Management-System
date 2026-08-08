/**
 * Severity/priority/status pills. Color mapping is semantic on purpose
 * (Critical=red, Major=amber, Minor=gray) — this is the single design
 * decision from Step 13 that matters most for usability, since QA staff
 * scan for red badges first when triaging a queue.
 */

type BadgeTone = "critical" | "major" | "minor" | "accent" | "success" | "neutral";

const TONE_STYLES: Record<BadgeTone, { bg: string; color: string }> = {
  critical: { bg: "var(--color-critical-bg)", color: "var(--color-critical)" },
  major: { bg: "var(--color-major-bg)", color: "var(--color-major)" },
  minor: { bg: "var(--color-minor-bg)", color: "var(--color-minor)" },
  accent: { bg: "var(--color-accent-bg)", color: "var(--color-accent)" },
  success: { bg: "var(--color-success-bg)", color: "var(--color-success)" },
  neutral: { bg: "#f3f4f6", color: "#374151" },
};

function toneFromSeverity(value: string | null | undefined): BadgeTone {
  if (value === "Critical") return "critical";
  if (value === "Major") return "major";
  if (value === "Minor") return "minor";
  return "neutral";
}

interface BadgeProps {
  label: string;
  tone?: BadgeTone;
}

export function Badge({ label, tone = "neutral" }: BadgeProps) {
  const { bg, color } = TONE_STYLES[tone];
  return (
    <span
      style={{
        display: "inline-block",
        padding: "4px 10px",
        borderRadius: "999px",
        fontSize: "12px",
        fontWeight: 600,
        background: bg,
        color,
      }}
    >
      {label}
    </span>
  );
}

export { toneFromSeverity };

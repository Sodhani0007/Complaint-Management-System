/**
 * The single most-reused component in the app — every field in the four
 * form sections is one of these. Handles the "Awaiting AI extraction..."
 * placeholder styling from the reference UI as a first-class visual state,
 * not just a generic empty input, so the user can tell "not filled yet" apart
 * from "filled with an empty value".
 */

interface FormFieldProps {
  label: string;
  value: string | number | null;
  onChange: (value: string) => void;
  type?: "text" | "date" | "number" | "textarea" | "select";
  options?: string[];
  unit?: string;
  placeholder?: string;
}

export function FormField({
  label,
  value,
  onChange,
  type = "text",
  options,
  unit,
  placeholder = "Awaiting AI extraction...",
}: FormFieldProps) {
  const displayValue = value ?? "";
  const isEmpty = value === null || value === "";

  const inputStyle: React.CSSProperties = {
    width: "100%",
    padding: "10px 12px",
    fontSize: "14px",
    fontFamily: "var(--font-sans)",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-sm)",
    background: "var(--color-surface)",
    color: isEmpty ? "var(--color-text-placeholder)" : "var(--color-text-primary)",
  };

  return (
    <div style={{ marginBottom: "16px" }}>
      <label
        style={{
          display: "block",
          fontSize: "13px",
          fontWeight: 500,
          color: "var(--color-text-primary)",
          marginBottom: "6px",
        }}
      >
        {label}
      </label>

      {type === "textarea" && (
        <textarea
          value={displayValue}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
          rows={3}
          style={{ ...inputStyle, resize: "vertical" }}
        />
      )}

      {type === "select" && (
        <select value={displayValue} onChange={(e) => onChange(e.target.value)} style={inputStyle}>
          <option value="" disabled>
            {placeholder}
          </option>
          {options?.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      )}

      {(type === "text" || type === "date" || type === "number") && (
        <div style={{ position: "relative" }}>
          <input
            type={type}
            value={displayValue}
            placeholder={placeholder}
            onChange={(e) => onChange(e.target.value)}
            style={{ ...inputStyle, paddingRight: unit ? "40px" : undefined }}
          />
          {unit && (
            <span
              style={{
                position: "absolute",
                right: "12px",
                top: "50%",
                transform: "translateY(-50%)",
                fontSize: "13px",
                color: "var(--color-text-secondary)",
              }}
            >
              {unit}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

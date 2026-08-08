interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary";
  disabled?: boolean;
  type?: "button" | "submit";
}

export function Button({ children, onClick, variant = "primary", disabled, type = "button" }: ButtonProps) {
  const isPrimary = variant === "primary";
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      style={{
        padding: "10px 20px",
        fontSize: "14px",
        fontWeight: 600,
        borderRadius: "var(--radius-sm)",
        border: isPrimary ? "none" : "1px solid var(--color-border)",
        background: isPrimary ? "var(--color-accent)" : "var(--color-surface)",
        color: isPrimary ? "#ffffff" : "var(--color-text-primary)",
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.6 : 1,
      }}
    >
      {children}
    </button>
  );
}

import { useRef, useState } from "react";

interface FileDropzoneProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

const ACCEPTED_EXTENSIONS = [".pdf", ".docx", ".txt", ".eml"];

export function FileDropzone({ onFileSelected, disabled }: FileDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;
    const file = e.dataTransfer.files?.[0];
    if (file) onFileSelected(file);
  };

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      style={{
        border: `2px dashed ${isDragging ? "var(--color-accent)" : "var(--color-border)"}`,
        borderRadius: "var(--radius-md)",
        background: isDragging ? "var(--color-accent-bg)" : "var(--color-bg)",
        padding: "32px 16px",
        textAlign: "center",
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.6 : 1,
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_EXTENSIONS.join(",")}
        style={{ display: "none" }}
        disabled={disabled}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onFileSelected(file);
          e.target.value = ""; // allow re-selecting the same file
        }}
      />
      <div style={{ fontSize: "24px", marginBottom: "8px" }}>☁️</div>
      <div style={{ fontSize: "14px", fontWeight: 500 }}>
        Drag &amp; drop complaint document here
      </div>
      <div style={{ fontSize: "13px", color: "var(--color-accent)", marginTop: "2px" }}>
        or click to browse
      </div>
      <div
        style={{
          marginTop: "16px",
          padding: "10px",
          background: "var(--color-success-bg)",
          color: "var(--color-success)",
          borderRadius: "var(--radius-sm)",
          fontSize: "12px",
        }}
      >
        Supported formats: PDF, DOCX, TXT, EML — Max file size: 10MB
      </div>
    </div>
  );
}

import type { ReactNode } from "react";
import styles from "./AxisReferenceBlock.module.css";

interface AxisReferenceBlockProps {
  label: string;
  color?: string;
  variant?: "full" | "compact";
  children: ReactNode;
}

/** Colored-left-border axis block shell, shared by the About page, onboarding
 * overlay, and map legend — each fills `children` with its own row content. */
export function AxisReferenceBlock({
  label,
  color,
  variant = "full",
  children,
}: AxisReferenceBlockProps) {
  return (
    <div
      className={`${styles.block} ${variant === "compact" ? styles.compact : ""}`}
      style={color ? { borderColor: color } : undefined}
    >
      <div className={styles.label}>{label}</div>
      {children}
    </div>
  );
}

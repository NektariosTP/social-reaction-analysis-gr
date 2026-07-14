import { useLang } from "../../hooks/useLang";
import { axisLabel, intensityLevel } from "../../i18n";
import styles from "./IntensityDots.module.css";

interface IntensityDotsProps {
  value: string | null | undefined;
  showLabel?: boolean;
}

const FILLED_CLASS = { 1: "filled1", 2: "filled2", 3: "filled3" } as const;

export function IntensityDots({ value, showLabel }: IntensityDotsProps) {
  const [lang] = useLang();
  const level = intensityLevel(value);
  if (!level) return null;

  return (
    <span className={styles.wrap}>
      <span className={styles.dots}>
        {[1, 2, 3].map((dot) => (
          <span
            key={dot}
            className={`${styles.dot} ${dot <= level ? styles[FILLED_CLASS[level]] : ""}`}
          />
        ))}
      </span>
      {showLabel && <span>{axisLabel(value, lang)}</span>}
    </span>
  );
}

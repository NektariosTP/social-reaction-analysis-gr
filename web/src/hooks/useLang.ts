import { useTranslation } from "react-i18next";
import type { Lang } from "../i18n";

/** Normalizes i18next's language code (e.g. "en-US") to our Lang union. */
export function useLang(): [Lang, (lang: Lang) => void] {
  const { i18n } = useTranslation();
  const lang: Lang = i18n.language?.startsWith("el") ? "el" : "en";
  const setLang = (next: Lang) => {
    void i18n.changeLanguage(next);
  };
  return [lang, setLang];
}

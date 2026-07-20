import "@testing-library/jest-dom/vitest";
import { beforeAll } from "vitest";
import i18n from "../i18n";

// Deterministic language for every test unless a test explicitly switches it.
beforeAll(async () => {
  await i18n.changeLanguage("en");
});

// jsdom doesn't implement scrollIntoView.
Element.prototype.scrollIntoView = Element.prototype.scrollIntoView ?? (() => {});

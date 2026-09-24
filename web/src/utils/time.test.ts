import { describe, expect, it } from "vitest";
import { daysUntil, formatAbsoluteDate } from "./time";

describe("daysUntil", () => {
  const now = new Date(2026, 8, 24, 12, 0, 0).getTime(); // 24 Sep 2026, local noon

  it("counts whole days to a future date ignoring time-of-day", () => {
    expect(daysUntil("2026-09-27T06:00:00", now)).toBe(3);
  });

  it("returns 0 for later the same calendar day", () => {
    expect(daysUntil("2026-09-24T23:00:00", now)).toBe(0);
  });
});

describe("formatAbsoluteDate", () => {
  it("formats as a numeric DD/MM/YYYY date", () => {
    const out = formatAbsoluteDate("2026-09-18T09:00:00", "en");
    expect(out).toMatch(/\d{2}\/\d{2}\/\d{4}/);
    expect(out).toContain("18");
    expect(out).toContain("09");
    expect(out).toContain("2026");
  });
});

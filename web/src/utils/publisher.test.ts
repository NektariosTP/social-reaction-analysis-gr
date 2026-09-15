import { describe, expect, it } from "vitest";
import { publisherFromUrl } from "./publisher";

describe("publisherFromUrl", () => {
  it("returns the host without a leading www.", () => {
    expect(publisherFromUrl("https://www.kathimerini.gr/politics/123/foo/")).toBe(
      "kathimerini.gr",
    );
  });

  it("returns the host as-is when there is no www.", () => {
    expect(publisherFromUrl("https://protothema.gr/greece/article")).toBe("protothema.gr");
  });

  it("keeps meaningful subdomains (only www. is stripped)", () => {
    expect(publisherFromUrl("https://news.example.gr/x")).toBe("news.example.gr");
  });

  it("lowercases the host", () => {
    expect(publisherFromUrl("https://WWW.EfSyn.GR/foo")).toBe("efsyn.gr");
  });

  it("returns null for a missing or unparseable URL", () => {
    expect(publisherFromUrl(null)).toBeNull();
    expect(publisherFromUrl(undefined)).toBeNull();
    expect(publisherFromUrl("")).toBeNull();
    expect(publisherFromUrl("not a url")).toBeNull();
  });
});

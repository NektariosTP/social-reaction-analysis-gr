import { useState } from "react";

const KEY = "reaction-map:onboarding-seen";

export function useOnboardingSeen() {
  const [seen, setSeen] = useState(() => localStorage.getItem(KEY) === "1");

  const dismiss = () => {
    localStorage.setItem(KEY, "1");
    setSeen(true);
  };

  return { seen, dismiss };
}

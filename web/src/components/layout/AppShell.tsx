import type { ReactNode } from "react";
import { TopBar } from "./TopBar";
import { Footer } from "./Footer";
import styles from "./AppShell.module.css";

/** Default page frame (TopBar + content + Footer) used by every route except
 * the main view's immersive mode, which goes full-bleed with its own chrome. */
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className={styles.shell}>
      <TopBar />
      <main className={styles.main}>{children}</main>
      <Footer />
    </div>
  );
}

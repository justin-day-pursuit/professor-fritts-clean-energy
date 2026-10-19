/**
 * The "Developer view" switch, shared between the hidden developer menu in the top bar and the report.
 *
 * Turning it on shows the code-style names (field names, flag names, calculation ids, tool names) in a report. It lives
 * outside any one component so the menu (in the top bar) and the report (further down the page) always agree.
 * It resets to off when the page is reloaded, so a visitor never sees it unless they switch it on again.
 */
import { useSyncExternalStore } from "react";

let on = false;
const listeners = new Set<() => void>();

export function setDevView(value: boolean) {
  on = value;
  listeners.forEach((listener) => listener());
}

/** The current setting and a way to change it. Re-renders the component whenever it changes. */
export function useDevView(): [boolean, (value: boolean) => void] {
  const value = useSyncExternalStore(
    (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    () => on,
    () => false,
  );
  return [value, setDevView];
}

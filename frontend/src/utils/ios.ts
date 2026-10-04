/**
 * Clear iOS's undo history for every input so shake-to-undo won't fire when the
 * phone is picked up mid-session. Toggling readonly drops an input's undo stack.
 */
export function clearUndoHistory(): void {
  document.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>("input, textarea").forEach((el) => {
    if (el.readOnly) return;
    el.setAttribute("readonly", "");
    el.removeAttribute("readonly");
  });
  (document.activeElement as HTMLElement | null)?.blur();
}

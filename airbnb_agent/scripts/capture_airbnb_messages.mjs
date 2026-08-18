/**
 * Read-only DOM capture helpers for the authorized Airbnb host message tables.
 *
 * This module is intentionally browser-runtime agnostic: pass the already
 * connected tab handles from the documented browser runner. It never sends a
 * message, edits a reservation, or reads cookies/passwords.
 */

import { appendFile, readFile, writeFile } from "node:fs/promises";

const THREAD_SELECTOR = '[data-testid^="inbox_list_"]';
const MESSAGE_SELECTOR = '[data-testid="MessageOuterRegistryWrapperSpacingProps"]';

export async function captureAirbnbTableIndex({ normalTab, archivedTab, outputPath }) {
  const [normal, archived] = await Promise.all([
    captureTable(normalTab, "normal"),
    captureTable(archivedTab, "archived"),
  ]);
  const payload = {
    captured_at: new Date().toISOString(),
    normal,
    archived,
  };
  await writeFile(outputPath, `${JSON.stringify(payload, null, 2)}\n`, { mode: 0o600 });
  return { normal: normal.length, archived: archived.length, outputPath };
}

export async function captureAirbnbThreadBatch({
  tab,
  scope,
  listUrl,
  threadRows,
  outputPath,
}) {
  const existing = await existingThreadIds(outputPath);
  const results = [];

  for (const row of threadRows) {
    const threadId = String(row.thread_id || "").trim();
    if (!threadId || existing.has(`${scope}:${threadId}`)) continue;

    try {
      const href = String(row.href || "").trim();
      if (href) {
        const threadUrl = new URL(href, "https://www.airbnb.com").href;
        await tab.goto(threadUrl);
      } else {
        const locator = tab.playwright.getByTestId(`inbox_list_${threadId}`);
        await locator.waitFor({ state: "visible", timeoutMs: 5000 });
        await locator.click();
      }
      await tab.playwright.waitForLoadState({ state: "domcontentloaded", timeoutMs: 10000 }).catch(() => {});
      await tab.playwright.waitForTimeout(250);
    } catch {
      results.push({ threadId, messageCount: 0, ok: false });
      continue;
    }

    let messages;
    let detailText;
    try {
      messages = await tab.playwright.locator(MESSAGE_SELECTOR).allTextContents({ timeoutMs: 5000 });
      detailText = await tab.playwright.locator("body").innerText({ timeoutMs: 5000 });
    } catch {
      results.push({ threadId, messageCount: 0, ok: false });
      continue;
    }
    const capture = {
      dataset: scope,
      thread_id: threadId,
      preview: row.text || "",
      messages,
      detail_text: detailText,
      captured_at: new Date().toISOString(),
      message_count: messages.length,
      message_chars: messages.reduce((total, message) => total + message.length, 0),
      ok: true,
    };
    await appendFile(outputPath, `${JSON.stringify(capture)}\n`, { mode: 0o600 });
    existing.add(`${scope}:${threadId}`);
    results.push({ threadId, messageCount: messages.length });

  }

  if (listUrl) {
    await tab.goto(listUrl);
    await tab.playwright.waitForLoadState({ state: "domcontentloaded", timeoutMs: 10000 }).catch(() => {});
  }

  return { scope, captured: results.length, results, outputPath };
}

async function captureTable(tab, scope) {
  return tab.playwright.locator(THREAD_SELECTOR).evaluateAll((elements, scopeName) => elements.map((element) => ({
    dataset: scopeName,
    thread_id: element.getAttribute("data-testid")?.replace("inbox_list_", "") || "",
    href: element.getAttribute("href") || "",
    text: (element.innerText || "").trim(),
    aria: element.getAttribute("aria-label") || "",
  })), scope);
}

async function existingThreadIds(outputPath) {
  try {
    const text = await readFile(outputPath, "utf8");
    return new Set(
      text
        .split("\n")
        .filter(Boolean)
        .map((line) => {
          try {
            const item = JSON.parse(line);
            return `${item.dataset || "unknown"}:${item.thread_id || ""}`;
          } catch {
            return "";
          }
        })
        .filter(Boolean),
    );
  } catch (error) {
    if (error?.code === "ENOENT") return new Set();
    throw error;
  }
}

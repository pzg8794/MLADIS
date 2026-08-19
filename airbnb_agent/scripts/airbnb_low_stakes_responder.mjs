/**
 * Guarded Airbnb inbox responder for an already-authorized host browser tab.
 *
 * It processes only rows Airbnb labels Unread, sends only decisions authorized
 * by MLADIS, rechecks the latest inbound message before clicking Send, and
 * records provider DOM evidence. Customer text stays in protected temp files.
 */

import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { chmod, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const THREAD_SELECTOR = '[data-testid^="inbox_list_"]';
const MESSAGE_SELECTOR = '[data-testid="MessageOuterRegistryWrapperSpacingProps"]';
const COMPOSER_SELECTOR = '[data-testid="messaging-composebar"]';
const SEND_SELECTOR = '[data-testid="messaging_compose_bar_send_button"]';

function digest(value) {
  return createHash("sha256").update(String(value || "").trim(), "utf8").digest("hex");
}

function normalize(value) {
  return String(value || "").replace(/\r\n/g, "\n").trim();
}

export class DjangoAutoResponseClient {
  constructor({ repositoryRoot, pythonPath }) {
    this.repositoryRoot = resolve(repositoryRoot);
    this.agentRoot = join(this.repositoryRoot, "airbnb_agent");
    this.managePath = join(this.agentRoot, "manage.py");
    this.pythonPath = resolve(pythonPath || join(this.agentRoot, ".venv", "bin", "python"));
  }

  prepare(payload, { authorizeLowStakes = false } = {}) {
    return this.#run("prepare", payload, { authorizeLowStakes });
  }

  claim(payload) {
    return this.#run("claim", payload);
  }

  complete(payload) {
    return this.#run("complete", payload);
  }

  uncertain(payload) {
    return this.#run("uncertain", payload);
  }

  async #run(action, payload, { authorizeLowStakes = false } = {}) {
    const directory = await mkdtemp(join(tmpdir(), "mladis-airbnb-response-"));
    await chmod(directory, 0o700);
    const inputPath = join(directory, "input.json");
    const outputPath = join(directory, "output.json");
    try {
      await writeFile(inputPath, `${JSON.stringify(payload)}\n`, { mode: 0o600 });
      const args = [
        this.managePath,
        "process_airbnb_auto_response",
        action,
        "--input",
        inputPath,
        "--output",
        outputPath,
      ];
      if (authorizeLowStakes) args.push("--authorize-low-stakes");
      await execFileAsync(this.pythonPath, args, {
        cwd: this.agentRoot,
        maxBuffer: 1024 * 1024,
      });
      return JSON.parse(await readFile(outputPath, "utf8"));
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  }
}

export async function processUnreadAirbnbMessages({
  tab,
  responseClient,
  send = false,
  maxThreads = 5,
}) {
  if (!tab?.playwright) throw new Error("An authorized Airbnb browser tab is required.");
  if (!responseClient) throw new Error("A MLADIS response client is required.");

  const rows = await tab.playwright.locator(THREAD_SELECTOR).evaluateAll((elements) =>
    elements
      .map((element) => ({
        threadId: (element.getAttribute("data-testid") || "").replace("inbox_list_", ""),
        preview: (element.textContent || "").trim(),
      }))
      .filter((row) => row.threadId && row.preview.startsWith("Unread.")),
  );
  const summary = {
    checked: 0,
    authorized: 0,
    sent: 0,
    held: 0,
    skipped: 0,
    uncertain: 0,
  };

  for (const row of rows.slice(0, Math.max(1, maxThreads))) {
    summary.checked += 1;
    await tab.goto(`https://www.airbnb.com/hosting/messages/${encodeURIComponent(row.threadId)}`);
    await tab.playwright.waitForLoadState({ state: "domcontentloaded", timeoutMs: 10000 }).catch(() => {});
    await tab.playwright.waitForTimeout(500);

    const before = await extractLatestHumanMessage(tab);
    if (!before || before.role !== "guest" || !before.text) {
      summary.skipped += 1;
      await restoreUnread(tab);
      continue;
    }
    const listingId = await extractListingId(tab);
    const decision = await responseClient.prepare(
      {
        thread_key: row.threadId,
        latest_message: before.text,
        listing_id: listingId,
        listing_hint: row.preview,
      },
      { authorizeLowStakes: send },
    );
    if (decision.status !== "authorized") {
      summary.held += 1;
      await restoreUnread(tab);
      continue;
    }
    summary.authorized += 1;

    const current = await extractLatestHumanMessage(tab);
    if (!current || current.role !== "guest" || digest(current.text) !== digest(before.text)) {
      summary.held += 1;
      await restoreUnread(tab);
      continue;
    }
    await responseClient.claim({
      authorization_id: decision.authorization_id,
      thread_key: row.threadId,
      latest_message: current.text,
      draft_hash: decision.draft_hash,
    });

    let clicked = false;
    try {
      const composer = tab.playwright.locator(COMPOSER_SELECTOR).getByRole("textbox");
      await composer.waitFor({ state: "visible", timeoutMs: 5000 });
      await composer.fill(decision.reply);
      const sendButton = tab.playwright.locator(SEND_SELECTOR);
      await sendButton.waitFor({ state: "visible", timeoutMs: 5000 });
      await sendButton.click();
      clicked = true;
      await tab.playwright.waitForTimeout(1500);
      const delivered = await extractLatestHumanMessage(tab);
      if (!delivered || delivered.role !== "host" || normalize(delivered.text) !== normalize(decision.reply)) {
        throw new Error("Provider DOM did not verify the sent response.");
      }
      await responseClient.complete({
        authorization_id: decision.authorization_id,
        provider_message_id: `dom-${digest(`${row.threadId}|${delivered.text}`).slice(0, 24)}`,
      });
      summary.sent += 1;
    } catch (error) {
      await responseClient.uncertain({
        authorization_id: decision.authorization_id,
        reason: clicked ? "send_clicked_delivery_unverified" : "send_not_completed",
      });
      summary.uncertain += 1;
    }
  }

  return summary;
}

export async function extractLatestHumanMessage(tab) {
  const records = await tab.playwright.locator(MESSAGE_SELECTOR).evaluateAll((elements) =>
    elements
      .map((element) => {
        const labels = [...element.querySelectorAll("button[aria-label]")]
          .map((button) => button.getAttribute("aria-label") || "");
        const sender = labels.find((label) => /(?:· Host|· Booker|· Guest)/.test(label)) || "";
        const role = /· Host/.test(sender)
          ? "host"
          : /· (?:Booker|Guest)/.test(sender)
            ? "guest"
            : "system";
        const content = element.querySelector('[data-name="message-content-wrapper"]');
        return { role, text: (content?.innerText || "").trim() };
      })
      .filter((record) => record.role !== "system" && record.text),
  );
  return records.at(-1) || null;
}

async function extractListingId(tab) {
  const hrefs = await tab.playwright.locator('a[href*="/rooms/"]').evaluateAll((elements) =>
    elements.map((element) => element.getAttribute("href") || ""),
  ).catch(() => []);
  for (const href of hrefs) {
    const match = href.match(/\/rooms\/(\d+)/);
    if (match) return match[1];
  }
  return "";
}

async function restoreUnread(tab) {
  const direct = tab.playwright.getByRole("button", { name: /mark as unread/i });
  if (await direct.count().catch(() => 0)) {
    await direct.first().click().catch(() => {});
    return;
  }
  const actions = tab.playwright.getByRole("button", {
    name: "Select to access additional buttons and actions",
  });
  if (!(await actions.count().catch(() => 0))) return;
  await actions.first().click().catch(() => {});
  const menuItem = tab.playwright.getByText(/mark as unread/i, { exact: false });
  if (await menuItem.count().catch(() => 0)) await menuItem.first().click().catch(() => {});
}

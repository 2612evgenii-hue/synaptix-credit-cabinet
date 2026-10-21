import test from "node:test";
import assert from "node:assert/strict";
import {
  blank,
  seed,
  schedule,
  quote,
  transition,
  validateApplication,
  terms,
  contractDocument,
} from "../src/domain";
const cents = (n: number) => Math.round(n * 100);
test("annuity reconciles principal, interest and final balance across catalogue bounds", () => {
  for (const amount of [10000, 300000, 1500000, 10000000])
    for (const months of [3, 6, 12, 24, 36])
      for (const rate of [0, 16, 18, 50]) {
        const q = quote(amount, months, rate);
        assert.equal(q.rows.length, months);
        assert.equal(q.rows.at(-1)?.balance, 0);
        assert.equal(
          q.rows.reduce((s, r) => s + cents(r.principal), 0),
          cents(amount),
        );
        assert.equal(cents(q.total), cents(amount) + cents(q.interest));
        assert(
          q.rows.every(
            (r) => r.balance >= 0 && r.principal > 0 && r.interest >= 0,
          ),
        );
      }
});
test("invalid numeric inputs never produce a repayment schedule", () => {
  for (const args of [
    [NaN, 12, 16],
    [Infinity, 12, 16],
    [-1, 12, 16],
    [1000, 1.5, 16],
    [1000, 0, 16],
    [1000, 121, 16],
    [1000, 12, -1],
    [1000, 12, NaN],
  ])
    assert.deepEqual(schedule(...(args as [number, number, number])), []);
});
test("zero is a valid declared debt, an empty field is missing data", () => {
  const a = seed().applications[1];
  assert.deepEqual(validateApplication(a), []);
  assert(
    validateApplication({ ...a, debt: "" }).some((e) =>
      e.includes("задолженность"),
    ),
  );
  assert(
    validateApplication({ ...a, amount: NaN }).some((e) => e.includes("сумму")),
  );
  assert(
    validateApplication({ ...a, months: 6.5 }).some((e) => e.includes("срок")),
  );
});
test("incomplete draft and accountant cannot submit", () => {
  assert.throws(() => transition(blank("TEST"), "review", "director", "test"));
  const a = { ...seed().applications[1], status: "draft" as const };
  assert.throws(() => transition(a, "review", "accountant", "test"));
  assert.equal(transition(a, "review", "director", "test").status, "review");
});
test("decision, signature, readiness and issue remain separate role-controlled events", () => {
  let a = seed().applications[1];
  assert.throws(() => transition(a, "issued", "bank", "test"));
  assert.throws(() => transition(a, "approved", "director", "test"));
  a = transition(
    { ...a, offerAmount: 2000000, offerMonths: 18, offerRate: 17, version: 2 },
    "alternative",
    "bank",
    "offered",
  );
  assert.equal(a.drawn, 0);
  assert.equal(terms(a).amount, 2000000);
  assert.throws(() => transition(a, "ready", "bank", "test"));
  a = transition(a, "signed", "director", "signed");
  assert.throws(() =>
    transition({ ...a, signedVersion: 1 }, "ready", "bank", "test"),
  );
  a = transition({ ...a, signedVersion: 2 }, "ready", "bank", "ready");
  assert.equal(a.drawn, 0);
  a = transition(a, "issued", "director", "issue");
  assert.throws(() => transition(a, "issued", "director", "duplicate"));
  assert.equal(a.history.at(-1)?.actor, "Руководитель");
});
test("rejection is final and request returns the same application to review", () => {
  const a = seed().applications[1];
  const requested = transition(a, "needs_info", "bank", "request");
  assert.equal(transition(requested, "review", "director", "reply").id, a.id);
  assert.throws(() =>
    transition(
      transition(a, "rejected", "bank", "rejected"),
      "approved",
      "bank",
      "test",
    ),
  );
});
test("one document generator distinguishes line duration from first draw", () => {
  const a = {
    ...blank("TEST", "line", 1500000, 6),
    requestedDraw: 700000,
    version: 2,
    signedVersion: 2,
  };
  const doc = contractDocument(a);
  assert.match(doc.data, /Срок первого транша: 6 месяцев/);
  assert.match(doc.data, /Срок линии: 24 месяца/);
  assert.equal(doc.status, "accepted");
  assert.equal(contractDocument({ ...a, version: 3 }).status, "added");
});

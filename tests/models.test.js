const test = require("node:test");
const assert = require("node:assert/strict");
const models = require("../app/models/core.js");

test("composite risk is deterministic and bounded", () => {
  assert.equal(models.compositeRisk({ severity: 5, velocity: 80, exposure: 70, concentration: 60, confidence: "High" }), 82);
  assert.throws(() => models.compositeRisk({ severity: 6, velocity: 80, exposure: 70, concentration: 60, confidence: "High" }), /severity/);
});

test("attention priority does not infer controls from recommended actions", () => {
  const base = models.attentionPriority({ score: 80, deadlineDays: 30, evidenceConfidence: "High" });
  const repeated = models.attentionPriority({ score: 80, deadlineDays: 30, evidenceConfidence: "High", actions: [1, 2, 3, 4] });
  assert.equal(base, repeated);
});

test("breach engine only emits evaluated rules", () => {
  const now = Date.parse("2026-08-30T00:00:00Z");
  const out = models.evaluateBreaches([
    { id: "a", score: 70, delta: 1, severity: 4, confidence: "High", thresholds: ["price moves"] },
    { id: "b", score: 84, delta: 2, severity: 4, confidence: "Medium" }
  ], [], now);
  assert.equal(out.length, 1);
  assert.equal(out[0].riskId, "b");
  assert.equal(out[0].observed, 84);
  assert.equal(out[0].limit, 80);
});

test("pressure index cannot be mistaken for a probability", () => {
  const result = models.pressureIndex({ score: 80, velocity: 70, tailScore: 60, deadlineProximity: 50 });
  assert.equal(result.calibrated, false);
  assert.equal(result.isProbability, false);
  assert.ok(result.index0to100 >= 3 && result.index0to100 <= 90);
  assert.equal("probability" in result, false);
});

test("ensemble reports disagreement without a decision floor", () => {
  const result = models.ensembleSummary({ rules: 20, quant: 30, stress: 90, network: 40, pressure: 50 });
  assert.deepEqual({ min: result.min, median: result.median, max: result.max }, { min: 20, median: 40, max: 90 });
  assert.equal(result.decisionReady, false);
});

test("control strength requires tested control evidence", () => {
  assert.equal(models.controlStrength([]), null);
  assert.equal(models.controlStrength([{ designEffective: true, operatingEffective: true }]), null);
  assert.equal(models.controlStrength([{ evidenceId: "ev-1", testedAt: "2026-08-01", designEffective: true, operatingEffective: false }]), 50);
});

test("Ind AS 109 diagnostics expose evidence and never apply an 80-125 bright line", () => {
  const result = models.indAs109Diagnostics({
    exposureChanges: [1, 2, -1, 3],
    hedgeChanges: [-1, -2, 1, -3],
    creditRiskDominates: false,
    hedgeRatioDocumented: true
  });
  assert.equal(result.brightLineApplied, false);
  assert.equal(result.conclusion, "documented-judgement-required");
  assert.equal(result.correlation, -1);
});

test("stress engine keeps consumer cost and producer revenue channels separate", () => {
  const result = models.stressChannels({
    shockPct: 10,
    costExposureInr: 1000,
    revenueExposureInr: 500,
    hedgeCoveragePct: 20,
    customerPassThroughPct: 50,
    producerRealisationPct: 80
  });
  assert.equal(result.costLossInr, 40);
  assert.equal(result.producerBenefitInr, 32);
  assert.equal(result.netPnlInr, -8);
  assert.equal(result.channelsCombined, false);
});

test("portfolio CFaR uses supplied positions, live vols, and correlations", () => {
  const result = models.portfolioCfar([
    { factor: "crude", amountInr: 1000, sensitivitySign: 1, hedgeCoveragePct: 0 },
    { factor: "usdinr", amountInr: 500, sensitivitySign: 1, hedgeCoveragePct: 20 }
  ], {
    vols: { crude: { monthly: 0.10 }, usdinr: { monthly: 0.02 } },
    corr: { "crude|usdinr": 0.25 }
  }, { horizonMonths: 1 });
  assert.equal(result.available, true);
  assert.equal(result.includedRows, 2);
  assert.ok(result.cfArInr > 160 && result.cfArInr < 180);
  assert.equal(result.validated, false);
});

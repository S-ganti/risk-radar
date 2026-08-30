(function (root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.RiskModels = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const CONFIDENCE = { High: 90, Medium: 60, Low: 30 };
  const Z95 = 1.6448536269514722;

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function finite(value, label) {
    const number = Number(value);
    if (!Number.isFinite(number)) throw new TypeError(`${label} must be finite`);
    return number;
  }

  function bounded(value, label, min = 0, max = 100) {
    const number = finite(value, label);
    if (number < min || number > max) throw new RangeError(`${label} must be between ${min} and ${max}`);
    return number;
  }

  function confidenceValue(value) {
    if (typeof value === "string") return CONFIDENCE[value] || 0;
    return bounded(value, "confidence");
  }

  function compositeRisk(input) {
    const severity = bounded(input.severity, "severity", 1, 5) / 5 * 100;
    const velocity = bounded(input.velocity, "velocity");
    const exposure = bounded(input.exposure, "exposure");
    const concentration = bounded(input.concentration, "concentration");
    const confidence = confidenceValue(input.confidence);
    return Math.round(
      0.30 * severity +
      0.20 * velocity +
      0.25 * exposure +
      0.15 * concentration +
      0.10 * confidence
    );
  }

  function deadlineProximity(days) {
    if (days === null || days === undefined) return 20;
    return clamp(100 - finite(days, "deadlineDays") / 3.65, 0, 100);
  }

  function attentionPriority(input) {
    const score = bounded(input.score, "score");
    const urgency = deadlineProximity(input.deadlineDays);
    const evidenceConfidence = confidenceValue(input.evidenceConfidence);
    const evidenceGap = 100 - evidenceConfidence;
    return Math.round((0.65 * score + 0.20 * urgency + 0.15 * evidenceGap) * 10) / 10;
  }

  function evaluateBreaches(risks, calendar, nowMs) {
    const now = Number.isFinite(nowMs) ? nowMs : Date.now();
    const results = [];
    (risks || []).forEach((risk) => {
      const score = bounded(risk.score, `${risk.id || "risk"}.score`);
      const delta = finite(risk.delta || 0, `${risk.id || "risk"}.delta`);
      const scoreLimit = risk.scoreLimit === undefined ? 80 : bounded(risk.scoreLimit, "scoreLimit");
      const deltaLimit = risk.deltaLimit === undefined ? 10 : bounded(risk.deltaLimit, "deltaLimit", 0, 100);
      if (score > scoreLimit) {
        results.push({
          id: `${risk.id}:score`, riskId: risk.id, severity: "urgent", rule: "risk-score",
          label: "Risk score above limit", observed: score, limit: scoreLimit, unit: "score",
          source: "computed composite"
        });
      }
      if (delta > deltaLimit) {
        results.push({
          id: `${risk.id}:delta`, riskId: risk.id, severity: "warning", rule: "score-move",
          label: "Score increase above limit", observed: delta, limit: deltaLimit, unit: "points",
          source: "computed score history"
        });
      }
      if (risk.confidence === "Low" && finite(risk.severity, "severity") >= 4) {
        results.push({
          id: `${risk.id}:evidence`, riskId: risk.id, severity: "warning", rule: "evidence-gap",
          label: "High impact with low-confidence evidence", observed: "Low", limit: "Medium", unit: "confidence",
          source: "evidence registry"
        });
      }
    });
    (calendar || []).forEach((event) => {
      if (!event.date) return;
      const due = new Date(`${event.date}T00:00:00Z`).getTime();
      if (!Number.isFinite(due)) return;
      const days = Math.ceil((due - now) / 86400000);
      const limit = event.warningDays === undefined ? 30 : finite(event.warningDays, "warningDays");
      if (days >= 0 && days <= limit) {
        results.push({
          id: `deadline:${event.id || event.date}`, eventId: event.id, severity: "urgent", rule: "deadline",
          label: "Regulatory deadline inside warning window", observed: days, limit, unit: "days",
          source: event.source || "regulatory calendar"
        });
      }
    });
    const rank = { urgent: 0, warning: 1 };
    return results.sort((a, b) => rank[a.severity] - rank[b.severity] || String(a.id).localeCompare(String(b.id)));
  }

  function pressureIndex(input) {
    const score = bounded(input.score, "score");
    const velocity = bounded(input.velocity, "velocity");
    const tailScore = bounded(input.tailScore, "tailScore");
    const deadline = bounded(input.deadlineProximity, "deadlineProximity");
    const z = 0.5 * (score - 70) / 15 +
      0.3 * (velocity - 55) / 25 +
      0.2 * (tailScore - 55) / 25 +
      0.25 * (deadline - 60) / 40 - 0.55;
    return {
      index0to100: Math.round(clamp(100 / (1 + Math.exp(-z)), 3, 90)),
      logit: Math.round(z * 100) / 100,
      calibrated: false,
      isProbability: false
    };
  }

  function ensembleSummary(models) {
    const entries = Object.entries(models || {}).map(([id, value]) => ({
      id,
      score: bounded(typeof value === "number" ? value : value.score, `${id}.score`)
    }));
    if (!entries.length) throw new RangeError("at least one model score is required");
    const sorted = entries.map((entry) => entry.score).sort((a, b) => a - b);
    const mean = sorted.reduce((sum, score) => sum + score, 0) / sorted.length;
    const variance = sorted.reduce((sum, score) => sum + (score - mean) ** 2, 0) / sorted.length;
    return {
      median: sorted[Math.floor(sorted.length / 2)],
      mean: Math.round(mean * 10) / 10,
      min: sorted[0],
      max: sorted[sorted.length - 1],
      dispersion: Math.round(Math.sqrt(variance) * 10) / 10,
      componentCount: entries.length,
      calibrated: false,
      decisionReady: false
    };
  }

  function controlStrength(controls) {
    if (!Array.isArray(controls) || controls.length === 0) return null;
    const scored = controls.filter((control) => control && control.evidenceId && control.testedAt);
    if (!scored.length) return null;
    const value = scored.reduce((sum, control) => {
      const design = control.designEffective === true ? 50 : 0;
      const operation = control.operatingEffective === true ? 50 : 0;
      return sum + design + operation;
    }, 0) / scored.length;
    return Math.round(value);
  }

  function correlation(xs, ys) {
    if (!Array.isArray(xs) || !Array.isArray(ys) || xs.length !== ys.length || xs.length < 3) return null;
    const x = xs.map((value) => finite(value, "exposureReturn"));
    const y = ys.map((value) => finite(value, "hedgeReturn"));
    const mx = x.reduce((a, b) => a + b, 0) / x.length;
    const my = y.reduce((a, b) => a + b, 0) / y.length;
    let covariance = 0;
    let varianceX = 0;
    let varianceY = 0;
    for (let i = 0; i < x.length; i += 1) {
      const dx = x[i] - mx;
      const dy = y[i] - my;
      covariance += dx * dy;
      varianceX += dx * dx;
      varianceY += dy * dy;
    }
    if (!varianceX || !varianceY) return null;
    return covariance / Math.sqrt(varianceX * varianceY);
  }

  function indAs109Diagnostics(input) {
    const exposure = input.exposureChanges || [];
    const hedge = input.hedgeChanges || [];
    const corr = correlation(exposure, hedge);
    let slope = null;
    let rSquared = null;
    let dollarOffset = null;
    if (corr !== null) {
      const mx = exposure.reduce((a, b) => a + Number(b), 0) / exposure.length;
      const my = hedge.reduce((a, b) => a + Number(b), 0) / hedge.length;
      let covariance = 0;
      let varianceX = 0;
      for (let i = 0; i < exposure.length; i += 1) {
        covariance += (Number(exposure[i]) - mx) * (Number(hedge[i]) - my);
        varianceX += (Number(exposure[i]) - mx) ** 2;
      }
      slope = varianceX ? covariance / varianceX : null;
      rSquared = corr ** 2;
      const exposureTotal = exposure.reduce((a, b) => a + Number(b), 0);
      const hedgeTotal = hedge.reduce((a, b) => a + Number(b), 0);
      dollarOffset = exposureTotal ? -hedgeTotal / exposureTotal : null;
    }
    return {
      observations: Math.min(exposure.length, hedge.length),
      correlation: corr === null ? null : Math.round(corr * 10000) / 10000,
      regressionSlope: slope === null ? null : Math.round(slope * 10000) / 10000,
      rSquared: rSquared === null ? null : Math.round(rSquared * 10000) / 10000,
      dollarOffset: dollarOffset === null ? null : Math.round(dollarOffset * 10000) / 10000,
      economicRelationshipEvidence: corr === null ? "insufficient-data" : Math.abs(corr) >= 0.6 ? "supportive" : "weak",
      creditRiskAssessment: input.creditRiskDominates === true ? "dominates" : input.creditRiskDominates === false ? "does-not-dominate" : "not-assessed",
      hedgeRatioAssessment: input.hedgeRatioDocumented === true ? "documented" : "not-documented",
      conclusion: "documented-judgement-required",
      brightLineApplied: false,
      standard: "Ind AS 109 paragraph 6.4.1"
    };
  }

  function stressChannels(input) {
    const shock = finite(input.shockPct, "shockPct") / 100;
    const hedge = 1 - bounded(input.hedgeCoveragePct || 0, "hedgeCoveragePct") / 100;
    const costExposure = Math.max(0, finite(input.costExposureInr || 0, "costExposureInr"));
    const revenueExposure = Math.max(0, finite(input.revenueExposureInr || 0, "revenueExposureInr"));
    const costPassThrough = 1 - bounded(input.customerPassThroughPct || 0, "customerPassThroughPct") / 100;
    const revenuePassThrough = bounded(input.producerRealisationPct === undefined ? 100 : input.producerRealisationPct, "producerRealisationPct") / 100;
    const costLossInr = costExposure * shock * hedge * costPassThrough;
    const producerBenefitInr = revenueExposure * shock * hedge * revenuePassThrough;
    return {
      costLossInr: Math.round(costLossInr),
      producerBenefitInr: Math.round(producerBenefitInr),
      netPnlInr: Math.round(producerBenefitInr - costLossInr),
      denominator: "currency amount supplied by user",
      channelsCombined: false
    };
  }

  function correlationLookup(correlations, a, b) {
    if (a === b) return 1;
    const direct = correlations[`${a}|${b}`];
    const reverse = correlations[`${b}|${a}`];
    const value = direct === undefined ? reverse : direct;
    return value === undefined || value === null ? 0 : clamp(finite(value, "correlation"), -1, 1);
  }

  function portfolioCfar(rows, market, options) {
    const opts = options || {};
    const horizonMonths = finite(opts.horizonMonths || 1, "horizonMonths");
    if (horizonMonths <= 0) throw new RangeError("horizonMonths must be positive");
    const vols = market && market.vols ? market.vols : {};
    const correlations = market && market.corr ? market.corr : {};
    const usable = (rows || []).map((row, index) => {
      const factor = String(row.factor || "").trim();
      const vol = vols[factor] && finite(vols[factor].monthly, `${factor}.monthlyVol`);
      if (!factor || !vol) return null;
      const amount = finite(row.amountInr, `row${index}.amountInr`);
      const sign = finite(row.sensitivitySign, `row${index}.sensitivitySign`);
      const hedge = 1 - bounded(row.hedgeCoveragePct || 0, `row${index}.hedgeCoveragePct`) / 100;
      return { factor, signedSensitivity: amount * sign * hedge, vol };
    }).filter(Boolean);
    if (!usable.length) return { available: false, reason: "no rows have both a valid amount and a market volatility" };
    let variance = 0;
    for (let i = 0; i < usable.length; i += 1) {
      for (let j = 0; j < usable.length; j += 1) {
        variance += usable[i].signedSensitivity * usable[j].signedSensitivity *
          usable[i].vol * usable[j].vol * correlationLookup(correlations, usable[i].factor, usable[j].factor);
      }
    }
    variance = Math.max(0, variance * horizonMonths);
    return {
      available: true,
      confidence: 0.95,
      horizonMonths,
      cfArInr: Math.round(Z95 * Math.sqrt(variance)),
      volatilityInr: Math.round(Math.sqrt(variance)),
      includedRows: usable.length,
      method: "variance-covariance normal approximation",
      validated: false
    };
  }

  return {
    CONFIDENCE,
    clamp,
    compositeRisk,
    deadlineProximity,
    attentionPriority,
    evaluateBreaches,
    pressureIndex,
    ensembleSummary,
    controlStrength,
    indAs109Diagnostics,
    stressChannels,
    portfolioCfar
  };
});

# Plan Draft

## Objective
Expose terminalApi’s existing `pv-insight` detect action on the SDK TerminalClient (Python + JavaScript), matching the live UI caller. No new schemas, params, or conventions.

**Done means:** BC-1 and BC-3 pass against the live stack. If they fail, the work is not done.

## Canonical sources (copy — do not invent)

| Concern | Source of truth |
|--------|------------------|
| Gateway | `platform/services/terminalApi/app.py` — `action == 'pv-insight'` → `run_pv_insight_synthesis` |
| Request body | `platform/ui/modules/maintenance-ooda.js` `handlePVInsightQuery` — `{ action: 'pv-insight', detection, user_query }` |
| Response | `run_pv_insight_synthesis` → `create_response(200, { detection, llm_analysis })` |
| JEPA fixture + asserts | `platform/ui/tests/test_pv_insight_e2e_behavioral.js` Step 3 |
| Invalid input | same handler: missing `detection` → 400; invalid `severity_label` → 400 |
| Python method pattern | `sdk/python/ona_platform/services/terminal.py` `run_detection` |
| JS method pattern | `sdk/javascript/src/services/TerminalClient.js` `runDetection` |
| TS types pattern | `sdk/javascript/src/types/index.d.ts` `DetectionParams` + `runDetection` |
| Test file placement | `sdk/python/tests/test_terminal_client.py`, `sdk/javascript/tests/terminal.test.js` |
| Inline live-shaped fixture style | `sdk/javascript/tests/partnerApi.test.js` (“Sample payload matching the live…”) |
| Live call timeout (JS) | UI e2e `req.setTimeout(90000, …)` + SDK `Config` `timeout` option (`javascript/src/config.js`) |
| Live call timeout (Python) | `OnaConfig.timeout` default **120s** (`python/ona_platform/config.py`) — already ≥ e2e 90s |
| JS client/auth for live | `sdk/javascript/examples/terminal-api-example.js` (`OnaSDK`, AWS creds, `signRequest` path) |
| Python client/auth for live | `sdk/python/examples/terminal_ooda_example.py` (`OnaClient()`, env AWS) |
| JS live terminal base URL | UI e2e: host `api.asoba.co`, path `/terminal/detect` → SDK `endpoints.terminal = 'https://api.asoba.co/terminal'` |
| README bullets | Detection (Observe) lists in `javascript/README.md` / Terminal OODA in `python/README.md` |

Do **not** add `top_n` / `min_severity`. UI does not send them; terminalApi hardcodes them on pvInsight invoke.

## Files to change

1. `python/ona_platform/services/terminal.py` — after `list_detections`
2. `javascript/src/services/TerminalClient.js` — after `listDetections`
3. `javascript/src/types/index.d.ts` — next to `DetectionParams` / `runDetection`
4. `python/tests/test_terminal_client.py` — live BC-1 (+ secondary errors)
5. `javascript/tests/terminal.test.js` — live BC-3 (+ secondary errors)
6. `python/README.md` — Detection section, one bullet/example line like `run_detection`
7. `javascript/README.md` — under `**Detection (Observe):**`, add `- \`runPvInsightSynthesis(params)\` - Run pv-insight O&M synthesis` next to `runDetection`

## Implementation (exact)

### Python — copy `run_detection` transport; body from UI

Place in Detection (Observe). Docstring structure = `run_detection` (Args/Returns). Purpose sentence from terminalApi `run_pv_insight_synthesis` docstring (delegate to pvInsightService for RAG + Nehanda synthesis).

```python
def run_pv_insight_synthesis(
    self,
    detection: dict,
    user_query: str = "Analyze JEPA Anomaly & Recommend BOM",
) -> dict:
    import json
    payload = {
        'httpMethod': 'POST',
        'path': '/detect',
        'body': json.dumps({
            'action': 'pv-insight',
            'detection': detection,
            'user_query': user_query,
        })
    }
    return self.invoke_lambda(self.function_name, payload)
```

Default `user_query` string = `maintenance-ooda.js` default prompt. No client-side severity validation.

### JavaScript — copy `runDetection` transport; body from UI

```javascript
async runPvInsightSynthesis({ detection, user_query = 'Analyze JEPA Anomaly & Recommend BOM' }) {
  validateRequired({ detection }, ['detection']);
  return this.client.post(
    `${this.endpoint}/detect`,
    { action: 'pv-insight', detection, user_query },
    { signRequest: true }
  );
}
```

JSDoc structure = `runDetection`. `validateRequired` already imported in this file.

### TypeScript — same pattern as `DetectionParams`

```typescript
export interface PvInsightSynthesisParams {
  detection: any;
  user_query?: string;
}

// on TerminalClient, next to runDetection:
runPvInsightSynthesis(params: PvInsightSynthesisParams): Promise<any>;
```

(`detection: any` / `Promise<any>` matches existing TerminalClient looseness, e.g. `createIssue` / `runDetection` return types.)

## Verification (definition of done)

### Fixture (inline in both test files)

Copy exactly from `platform/ui/tests/test_pv_insight_e2e_behavioral.js`:

```javascript
const JEPA_DETECTION = {
  asset_id: 'INV-BN2441041190',
  severity_label: 'high',
  severity_score: 0.82,
  fault_type: 'behavioral_anomaly',
  summary: 'Inverter 1 - World model anomaly score 0.0891 (Streak: 6)',
  metrics: {
    latest_power_kw: 45.2,
    baseline_power_kw: 280.5,
    latest_temperature_c: 68.3,
    latest_inverter_state: 513,
    world_model_streak_length: 6
  },
  energy_at_risk_kw: 235.3
};
```

Same object in Python dict form in `test_terminal_client.py`.

### Asserts (copy from UI e2e Step 3)

On the SDK return value (Python: unwrapped body from `invoke_lambda`; JS: HTTP client JSON):

- `llm_analysis` is present
- `llm_analysis.status === 'ok'` (Python: `== "ok"`)
- `recommendation` is a string with `length > 20`
- `cited_sources` is an array/list with `length > 0`

### BC-1 — Python live (`python/tests/test_terminal_client.py`)

- Client: `OnaClient()` as in `terminal_ooda_example.py` (env AWS; default timeout 120s)
- Call: `client.terminal.run_pv_insight_synthesis(JEPA_DETECTION)`
- Assert: Step 3 checks above
- **Pass = objective met for Python**

### BC-3 — JavaScript live (`javascript/tests/terminal.test.js`)

- Client: `OnaSDK` as in `terminal-api-example.js`, with:
  - `endpoints.terminal: 'https://api.asoba.co/terminal'` (UI e2e host + `/terminal` prefix)
  - `timeout: 90000` (UI e2e 90s; overrides JS default 30s)
  - AWS credentials from env as in the example
- Call: `sdk.terminal.runPvInsightSynthesis({ detection: JEPA_DETECTION })`
- Assert: Step 3 checks above
- **Pass = objective met for JavaScript**

### Secondary (not equal weight to done)

In the same terminal test files, using terminalApi’s existing 400 rules:

1. Missing/empty `detection` → error via existing SDK error handling (`ValidationError` / HTTP client error)
2. `detection` with invalid `severity_label` (e.g. `'nope'`) → same

No mocked request-shape tests as proof of done.

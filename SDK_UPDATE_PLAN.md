# SDK Update Plan: Non-Admin Services Support

## Executive Summary

Update the Ona SDK to achieve feature parity between JavaScript and Python implementations, with enhanced support for OODA terminal services, forecasting, interpolation, and meter interrogation services.

**Status:** JavaScript SDK is feature-complete. Python SDK needs critical updates to match.

---

## Critical Gaps Identified

### Python SDK Missing Operations

1. **Terminal Service - Asset Management**
   - Missing: `get_asset()` method

2. **Terminal Service - Act Phase (Critical)**
   - Missing: BOM operations (`build_bom()`, `list_boms()`)
   - Missing: Order operations (`create_order()`, `list_orders()`)
   - Missing: Tracking operations (`subscribe_tracking()`, `list_tracking()`)

3. **Interpolation Service - Both SDKs**
   - Only generic `interpolate()` method exists
   - Missing convenience methods for specific algorithms (spline, gaussian process, physics-based)

4. **Enphase/Huawei Clients - JavaScript**
   - Missing parameter validation
   - Generic method signatures need improvement

---

## Implementation Plan

### Phase 1: Python Terminal Client - Critical Updates

**Priority: HIGH - Achieves SDK parity**

**File:** `python/ona_platform/services/terminal.py`

Add missing methods after existing operations:

1. **Add `get_asset()` method** (after `add_asset()`, ~line 101)
   - Parameters: `customer_id`, `asset_id`
   - Action: `get`
   - Returns: Asset details

2. **Add BOM operations** (after `list_schedules()`, ~line 266)
   - `build_bom(customer_id, asset_id, schedule_id=None)` - Action: `build`
   - `list_boms(customer_id)` - Action: `list`
   - Returns: BOM details and list

3. **Add Order operations** (after BOM operations)
   - `create_order(customer_id, asset_id, bom_id=None)` - Action: `create`
   - `list_orders(customer_id)` - Action: `list`
   - Returns: Order details and list

4. **Add Tracking operations** (after Order operations)
   - `subscribe_tracking(customer_id, job_id)` - Action: `subscribe`
   - `list_tracking(customer_id)` - Action: `list`
   - Returns: Tracking subscription and list

**Pattern to follow:**
```python
def method_name(self, customer_id: str, ...) -> Dict[str, Any]:
    """Docstring with Args and Returns."""
    import json
    payload = {
        'httpMethod': 'POST',
        'path': '/endpoint',
        'body': json.dumps({
            'action': 'action_name',
            'customer_id': customer_id,
            ...
        })
    }
    return self.invoke_lambda(self.function_name, payload)
```

---

### Phase 2: Interpolation Service Enhancement

**Priority: MEDIUM - Improves developer experience**

#### JavaScript SDK

**File:** `javascript/src/services/InterpolationClient.js`

Add convenience methods after the generic `interpolate()` method:

1. `splineInterpolation({ customer_id, dataset_key, spline_type='cubic' })`
   - Calls `interpolate()` with method='spline'
   - Validates parameters
   - Returns interpolation result

2. `gaussianProcessInterpolation({ customer_id, dataset_key, kernel='rbf' })`
   - Calls `interpolate()` with method='gaussian_process'
   - Validates parameters
   - Returns interpolation result

3. `physicsBasedInterpolation({ customer_id, dataset_key })`
   - Calls `interpolate()` with method='physics_based'
   - Validates parameters
   - Returns interpolation result

#### Python SDK

**File:** `python/ona_platform/services/interpolation.py`

Add matching convenience methods:

1. `spline_interpolation(customer_id, dataset_key, spline_type='cubic')`
2. `gaussian_process_interpolation(customer_id, dataset_key, kernel='rbf')`
3. `physics_based_interpolation(customer_id, dataset_key)`

All methods call the base `interpolate()` method with appropriate parameters.

---

### Phase 3: TypeScript Definitions Update

**Priority: HIGH - Required for JavaScript SDK usability**

**File:** `javascript/src/types/index.d.ts`

Add type definitions for new operations:

1. **Terminal Client - Add missing method signature:**
   ```typescript
   getAsset(params: { customer_id: string; asset_id: string }): Promise<Asset>;
   ```

2. **Interpolation Client - Add interface and methods:**
   ```typescript
   export interface InterpolationParams {
     customer_id: string;
     dataset_key: string;
     method?: 'spline' | 'gaussian_process' | 'physics_based' | 'multi_output' | 'adaptive';
     spline_type?: 'linear' | 'cubic' | 'quintic';
     kernel?: string;
   }

   export interface InterpolationResult {
     status: string;
     s3_output_key: string;
     records_interpolated: number;
     method_used: string;
     execution_time_ms: number;
   }

   export class InterpolationClient {
     interpolate(params: InterpolationParams): Promise<InterpolationResult>;
     splineInterpolation(params: { customer_id: string; dataset_key: string; spline_type?: string }): Promise<InterpolationResult>;
     gaussianProcessInterpolation(params: { customer_id: string; dataset_key: string; kernel?: string }): Promise<InterpolationResult>;
     physicsBasedInterpolation(params: { customer_id: string; dataset_key: string }): Promise<InterpolationResult>;
   }
   ```

3. **Enphase/Huawei types:**
   ```typescript
   export interface EnphaseCollectionParams {
     site_id: string;
     customer_id?: string;
   }

   export interface HuaweiCollectionParams {
     plant_code: string;
     customer_id?: string;
   }
   ```

---

### Phase 4: Enphase/Huawei Client Enhancement (Optional)

**Priority: LOW - Current implementation works but can be improved**

**Files:**
- `javascript/src/services/EnphaseClient.js`
- `javascript/src/services/HuaweiClient.js`

**Changes:**
- Replace generic `getHistoricalData()` / `getRealTimeData()` with validated methods
- Add parameter validation using validators from `../utils/validators`
- Improve JSDoc documentation with specific parameter types
- Add examples in method documentation

---

### Phase 5: Examples and Documentation

**Priority: MEDIUM - Essential for adoption**

#### New Example Files to Create

1. **JavaScript Examples:**
   - `javascript/examples/interpolation-example.js`
     - Demonstrate all interpolation methods (spline, GP, physics-based)
     - Show S3 key handling and result retrieval

   - `javascript/examples/complete-ooda-workflow.js`
     - Full workflow: Detect → Diagnose → Schedule → BOM → Order → Track
     - Error handling examples

2. **Python Examples:**
   - `python/examples/interpolation_example.py`
     - All interpolation methods with S3 integration

   - `python/examples/complete_ooda_workflow.py`
     - Full Act phase workflow (BOM → Order → Track)
     - Integration with Observe/Orient/Decide phases

#### Documentation Updates

1. **Main README** (`README.md`)
   - Update Terminal API section with detailed OODA phase breakdown
   - Add Interpolation Services section with method descriptions
   - Add Meter Interrogation Services section

2. **Language-specific READMEs:**
   - Add API reference sections
   - Add usage examples for new operations
   - Document parameter types and return values

---

## Implementation Sequence

### Week 1: Core Functionality (Critical Path)

1. ✅ **Python Terminal Client** - Add 7 missing methods
2. ✅ **TypeScript Definitions** - Add all new types
3. ✅ **Testing** - Verify Python changes work end-to-end

### Week 2: Enhancement & Examples

1. ✅ **Interpolation Enhancement** - Add convenience methods (both SDKs)
2. ✅ **Examples** - Create comprehensive usage examples
3. ✅ **Documentation** - Update README files

### Week 3: Polish & Validation (Optional)

1. ✅ **Enphase/Huawei Enhancement** - Improve validation
2. ✅ **Integration Testing** - Test against live services
3. ✅ **Code Review** - Consistency check across SDKs

---

## Success Criteria

### Functional Completeness
- ✅ Python SDK has all Terminal operations (parity with JavaScript)
- ✅ Both SDKs have interpolation convenience methods
- ✅ TypeScript definitions cover all operations

### Code Quality
- ✅ All Python methods have type hints and docstrings
- ✅ All JavaScript methods have JSDoc comments
- ✅ Consistent error handling patterns

### Documentation
- ✅ Every new method documented with examples
- ✅ README files updated with API reference
- ✅ At least 2 comprehensive examples per SDK

---

## Critical Files for Implementation

### Phase 1 (Must-Have):
1. `python/ona_platform/services/terminal.py` - Add 7 methods (~150 LOC)
2. `javascript/src/types/index.d.ts` - Add types (~100 LOC)

### Phase 2 (Should-Have):
3. `javascript/src/services/InterpolationClient.js` - Add 3 methods (~80 LOC)
4. `python/ona_platform/services/interpolation.py` - Add 3 methods (~70 LOC)

### Phase 3 (Nice-to-Have):
5. `javascript/examples/complete-ooda-workflow.js` - New file
6. `python/examples/complete_ooda_workflow.py` - New file
7. `README.md` - Update service descriptions

---

## Risk Mitigation

**No Breaking Changes:** All changes are additive. Existing code continues to work.

**Backward Compatibility:**
- New methods added, no existing methods modified
- Default parameters used where appropriate
- TypeScript definitions maintain existing signatures

**Testing Strategy:**
- Unit tests for parameter validation
- Integration examples to verify end-to-end workflows
- Manual testing against live platform services (if available)

---

## Estimated Effort

- **Phase 1 (Critical):** 1-2 days
- **Phase 2 (Enhancement):** 2-3 days
- **Phase 3 (Documentation):** 2-3 days
- **Total:** 5-8 days for complete implementation

---

## API Design Decisions

### 1. Action-Based Pattern
Keep internal action-based implementation but expose high-level methods to users:
- ✅ Users call `buildBOM()` not `post('/bom', {action: 'build'})`
- ✅ Better IDE autocomplete and type safety
- ✅ Clearer API surface

### 2. Convenience Methods for Interpolation
Provide both generic and specific methods:
- Generic: `interpolate({...})` for power users
- Specific: `splineInterpolation({...})` for common cases
- ✅ Serves both simple and advanced use cases

### 3. Parameter Validation
- JavaScript: Use existing validators module
- Python: Type hints + runtime validation where critical
- ✅ Fail fast with clear error messages

---

## Platform Service Coverage

After implementation, SDK will fully support:

✅ **Terminal API (OODA):**
- Observe: Detection, Monitoring, Activities
- Orient: Diagnostics, Analysis
- Decide: Scheduling, Planning
- Act: BOM, Orders, Tracking (✨ NEW in Python)

✅ **Forecasting Service:**
- Device, Site, Customer forecasts
- Model metadata and metrics

✅ **Interpolation Service:**
- All 5 methods: Spline, GP, Physics, Multi-output, Adaptive (✨ ENHANCED)
- Weather-enriched interpolation

✅ **Meter Interrogation:**
- Enphase: Real-time + Historical collection
- Huawei: Real-time + Historical collection
- OODA CSV format output

---

## Notes

- **No admin services identified:** All services reviewed are customer-scoped, non-admin operations
- **Authentication:** Currently none on platform APIs; SDK supports AWS Signature v4 for future
- **Deployment:** No infrastructure changes needed; SDK-only updates

---

# Architectural Decision Record (ADR)

## Overview

This section provides defensive justification for each architectural decision in the SDK update plan, demonstrating adherence to established patterns, DRY principles, and sound engineering practices.

---

## Decision 1: Maintain Action-Based Internal Pattern

### Context
Platform services use an action-based POST pattern where a single endpoint handles multiple operations via an `action` parameter:
```json
POST /terminal/assets
{ "action": "list|add|get", "customer_id": "...", ... }
```

### Decision
**Keep the action-based pattern for internal SDK implementation while exposing high-level convenience methods to users.**

### Engineering Logic

**Pro:**
1. **Single Source of Truth:** One internal method per endpoint reduces code duplication
2. **Flexibility:** Easy to add new actions without changing SDK architecture
3. **Transparency:** Internal implementation mirrors platform API structure
4. **Maintenance:** Bug fixes in one place benefit all action-based calls

**Con:**
1. **User Experience:** Raw action parameters are less intuitive than named methods
2. **Type Safety:** Generic payloads reduce compile-time validation

### Solution: Best of Both Worlds
```python
# User-facing API (high-level convenience)
client.terminal.get_asset(customer_id, asset_id)

# Internal implementation (action-based)
def get_asset(self, customer_id: str, asset_id: str):
    return self._invoke_action('/assets', {
        'action': 'get',
        'customer_id': customer_id,
        'asset_id': asset_id
    })
```

### DRY Adherence
- ✅ **Reuses existing HTTP client:** No duplication of request logic
- ✅ **Reuses validation:** Single validation point per parameter type
- ✅ **Reuses error handling:** Centralized in base client

### Pattern Consistency
- ✅ **Matches existing Terminal methods:** JavaScript SDK already uses this pattern (lines 29-92 in TerminalClient.js)
- ✅ **Matches Python forecasting service:** Uses same `invoke_lambda()` pattern
- ✅ **Cross-language consistency:** Same architectural approach in both SDKs

### Defensive Justification
**Why not expose raw actions?**
- Users shouldn't need to know internal action semantics
- IDE autocomplete works better with named methods
- Type systems can validate parameters at compile time
- Breaking changes in platform action names don't affect user code

**Why not create separate endpoints?**
- Platform uses action-based routing; SDK should match
- Premature abstraction would create maintenance burden
- Action-based pattern is already proven in existing codebase

---

## Decision 2: Add Missing Python Methods (Parity with JavaScript)

### Context
JavaScript SDK has complete OODA workflow support. Python SDK missing:
- `get_asset()` (asset retrieval)
- BOM operations (build, list)
- Order operations (create, list)
- Tracking operations (subscribe, list)

### Decision
**Add missing methods to Python SDK, following exact same pattern as JavaScript SDK.**

### Engineering Logic

**Why parity is critical:**
1. **User Expectations:** Developers expect feature parity across SDKs
2. **Documentation Efficiency:** Single set of docs works for both languages
3. **Migration Path:** Users switching languages shouldn't lose functionality
4. **Completeness:** Partial OODA support is worse than no support (breaks workflows)

**Why now (not later):**
1. **Act phase is critical:** Detection/Diagnosis without remediation is incomplete
2. **Adoption blocker:** Missing features prevent production use
3. **Technical debt:** Gaps accumulate; better to address comprehensively

### DRY Adherence
- ✅ **Reuses BaseServiceClient:** All methods inherit `invoke_lambda()`
- ✅ **Reuses payload structure:** Same JSON format as existing methods
- ✅ **No code duplication:** Each method is ~15 LOC, all unique functionality

### Pattern Consistency

**Existing Pattern (Python, lines 38-56):**
```python
def list_assets(self, customer_id: str) -> List[Dict[str, Any]]:
    """List all assets for a customer."""
    payload = {
        'httpMethod': 'POST',
        'path': '/assets',
        'body': json.dumps({
            'action': 'list',
            'customer_id': customer_id
        })
    }
    result = self.invoke_lambda(self.function_name, payload)
    return result.get('assets', [])
```

**New Pattern (IDENTICAL structure):**
```python
def get_asset(self, customer_id: str, asset_id: str) -> Dict[str, Any]:
    """Get a specific asset."""
    payload = {
        'httpMethod': 'POST',
        'path': '/assets',
        'body': json.dumps({
            'action': 'get',
            'customer_id': customer_id,
            'asset_id': asset_id
        })
    }
    return self.invoke_lambda(self.function_name, payload)
```

**Consistency Check:**
- ✅ Same payload structure (httpMethod, path, body)
- ✅ Same JSON serialization approach
- ✅ Same docstring format (Args, Returns)
- ✅ Same type hints pattern
- ✅ Same return value handling

### Defensive Justification
**Why not refactor while adding?**
- Don't mix refactoring with feature additions (separate concerns)
- Existing pattern is proven and working
- Refactoring introduces risk; feature addition is lower risk
- Users benefit from consistency, not premature optimization

**Why not create a generic method?**
```python
# BAD: Generic method that handles all actions
def _asset_action(self, action, **kwargs):
    # ... handles get, list, add
```
- ❌ Loses type safety
- ❌ Loses IDE autocomplete
- ❌ Loses clear documentation
- ❌ Harder to maintain (one big method vs many small methods)
- ❌ Doesn't follow existing codebase patterns

---

## Decision 3: Add Interpolation Convenience Methods

### Context
Current implementation has only generic `interpolate(payload)` method. Platform supports 5 distinct interpolation algorithms:
1. Spline (linear, cubic, quintic)
2. Gaussian Process (various kernels)
3. Physics-Based (solar-specific)
4. Multi-Output Regression (LightGBM)
5. Adaptive (auto-selects best method)

### Decision
**Add algorithm-specific convenience methods while keeping generic method for advanced users.**

### Engineering Logic

**User Experience Improvement:**
```python
# BEFORE: User must know internal method names
client.interpolation.interpolate({
    'customer_id': 'ABC',
    'dataset_key': 's3://...',
    'method': 'gaussian_process',  # How do I know this exists?
    'kernel': 'rbf'  # What are valid kernels?
})

# AFTER: Clear, discoverable API
client.interpolation.gaussian_process_interpolation(
    customer_id='ABC',
    dataset_key='s3://...',
    kernel='rbf'  # IDE autocomplete shows valid options
)
```

**Benefits:**
1. **Discoverability:** Users see available methods via IDE autocomplete
2. **Documentation:** Each method has specific docstring with algorithm details
3. **Validation:** Method-specific validation (e.g., kernel types for GP)
4. **Type Safety:** Clear parameter types, not generic dict
5. **Backward Compatibility:** Generic method still available for power users

### DRY Adherence
```python
# Base method (existing, unchanged)
def interpolate(self, payload: Dict) -> Dict:
    return self.client.post(self.endpoint, payload)

# Convenience methods (new, delegate to base)
def spline_interpolation(self, customer_id, dataset_key, spline_type='cubic'):
    return self.interpolate({
        'customer_id': customer_id,
        'dataset_key': dataset_key,
        'method': 'spline',
        'spline_type': spline_type
    })
```

**DRY Check:**
- ✅ **No logic duplication:** Convenience methods are parameter transformers
- ✅ **Single execution path:** All calls go through same `interpolate()` method
- ✅ **No copy-paste code:** Each method adds unique value (parameter mapping)
- ✅ **Maintainable:** Algorithm changes happen in platform, not SDK

### Pattern Consistency

**Precedent in Codebase:**
- ForecastingClient has `get_device_forecast()`, `get_site_forecast()`, `get_customer_forecast()`
  - All call same Lambda function with different parameters
  - Same pattern: convenience methods wrapping generic invocation
- TerminalClient has `run_detection()`, `list_detections()`
  - Different operations on same endpoint
  - Same pattern: high-level methods wrapping action-based calls

**Cross-SDK Consistency:**
- JavaScript and Python implementations will match
- Same method names, same parameters, same semantics
- Users switching languages have same experience

### Defensive Justification
**Why not just document the method parameter?**
```python
# BAD: Forces users to read docs, easy to typo
interpolate({'method': 'gaussain_process'})  # Oops, typo!
```
- ❌ No compile-time validation
- ❌ Documentation burden (users must reference external docs)
- ❌ Error-prone (method names are strings)
- ❌ Poor IDE support

**Why not use enums for method parameter?**
```python
# ALTERNATIVE: Enum-based approach
interpolate({'method': InterpolationMethod.GAUSSIAN_PROCESS})
```
- ⚠️ Better than strings, but still requires users to know:
  - Which parameters are valid for which method
  - What each method does
  - How to configure method-specific options
- ⚠️ Less discoverable than dedicated methods
- ⚠️ Doesn't solve parameter validation problem

**Convenience methods are objectively superior:**
- ✅ Type-safe parameters
- ✅ Method-specific documentation
- ✅ IDE autocomplete for parameters
- ✅ Compile-time validation
- ✅ Follows existing patterns in codebase

---

## Decision 4: Update TypeScript Definitions

### Context
JavaScript SDK has TypeScript definitions at `src/types/index.d.ts` for type safety and IDE support.

### Decision
**Add TypeScript interfaces and method signatures for all new operations.**

### Engineering Logic

**Type Safety Benefits:**
1. **Compile-time errors:** Catch mistakes before runtime
2. **IDE Integration:** Autocomplete, parameter hints, inline documentation
3. **Refactoring Safety:** TypeScript compiler catches breaking changes
4. **Self-Documentation:** Types serve as always-up-to-date API reference

**Example Impact:**
```typescript
// WITHOUT types: No compile-time validation
const result = await client.terminal.buildBOM({
  custmer_id: 'ABC',  // Typo! Runtime error
  asset_id: 123  // Wrong type! Runtime error
});

// WITH types: Errors caught at compile time
const result = await client.terminal.buildBOM({
  customer_id: 'ABC',  // ✓ Correct
  asset_id: '123'  // ✓ Type-safe
});
```

### DRY Adherence
- ✅ **Single source of truth:** Types defined once, used everywhere
- ✅ **No duplicate documentation:** Types ARE documentation
- ✅ **Automatic IDE integration:** No manual docs needed for basic usage

### Pattern Consistency

**Existing Pattern (lines 1-50 in index.d.ts):**
```typescript
export class ForecastingClient {
  getDeviceForecast(params: {
    site_id: string;
    device_id: string;
    forecast_hours?: number;
  }): Promise<DeviceForecast>;
}
```

**New Pattern (IDENTICAL structure):**
```typescript
export class InterpolationClient {
  splineInterpolation(params: {
    customer_id: string;
    dataset_key: string;
    spline_type?: string;
  }): Promise<InterpolationResult>;
}
```

**Consistency Check:**
- ✅ Same parameter object pattern
- ✅ Same optional parameter syntax (?)
- ✅ Same Promise return type pattern
- ✅ Same interface naming convention

### Defensive Justification
**Why not use JSDoc instead of TypeScript?**
```javascript
/**
 * @param {Object} params
 * @param {string} params.customer_id
 * @param {string} params.dataset_key
 */
async splineInterpolation(params) { ... }
```
- ❌ No compile-time validation
- ❌ No IDE autocomplete (most editors)
- ❌ Easy to get out of sync with implementation
- ✅ TypeScript definitions are enforced by compiler

**Why not generate types from code?**
- ⚠️ Possible, but adds build complexity
- ⚠️ Generated types often less readable
- ⚠️ Harder to maintain custom documentation
- ✅ Hand-written types allow better DX (developer experience)

**Why types are non-negotiable:**
- JavaScript SDK already has comprehensive types
- Removing types would be a regression
- TypeScript adoption is industry standard
- Users expect type definitions in modern JS libraries

---

## Decision 5: Create Comprehensive Examples

### Context
Current SDK has minimal examples. Complex workflows (full OODA cycle, interpolation pipelines) are undocumented.

### Decision
**Create example files demonstrating complete workflows and integration patterns.**

### Engineering Logic

**Educational Value:**
1. **Onboarding:** New users learn by example
2. **Best Practices:** Examples show recommended patterns
3. **Integration Testing:** Examples serve as informal integration tests
4. **Documentation:** Working code is better than written docs

**Specific Examples Needed:**
1. **Complete OODA Workflow:**
   - Demonstrates: Detect → Diagnose → Schedule → BOM → Order → Track
   - Value: Shows how services integrate in real-world scenario
   - Gap filled: Act phase (BOM/Order/Track) has no examples

2. **Interpolation Pipeline:**
   - Demonstrates: All interpolation methods with S3 integration
   - Value: Shows when to use each algorithm
   - Gap filled: Interpolation service has no examples

3. **Meter Interrogation:**
   - Demonstrates: Enphase/Huawei data collection
   - Value: Shows OAuth flow, error handling, result processing
   - Gap filled: Meter services have no examples

### DRY Adherence
- ✅ **Examples use SDK, not duplicate logic:** All examples import and use SDK methods
- ✅ **Examples don't reimplement SDK:** They demonstrate usage, not implementation
- ✅ **Shared patterns:** Error handling, logging, configuration are consistent across examples

### Pattern Consistency

**Existing Example Pattern (forecasting-example.js):**
```javascript
const { OnaSDK } = require('@asoba/ona-sdk');

async function main() {
  // Initialize SDK
  const sdk = new OnaSDK({ /* config */ });

  try {
    // Use SDK method
    const result = await sdk.forecasting.getDeviceForecast({...});
    console.log('Result:', result);
  } catch (error) {
    console.error('Error:', error.message);
  }
}

main();
```

**New Example Pattern (IDENTICAL structure):**
```javascript
const { OnaSDK } = require('@asoba/ona-sdk');

async function main() {
  const sdk = new OnaSDK({ /* config */ });

  try {
    // Full OODA workflow
    const detection = await sdk.terminal.runDetection({...});
    const diagnostic = await sdk.terminal.runDiagnostics({...});
    const schedule = await sdk.terminal.createSchedule({...});
    const bom = await sdk.terminal.buildBOM({...});
    const order = await sdk.terminal.createOrder({...});
    const tracking = await sdk.terminal.subscribeTracking({...});

    console.log('OODA cycle complete:', tracking);
  } catch (error) {
    console.error('Workflow failed:', error.message);
  }
}

main();
```

**Consistency Check:**
- ✅ Same imports and initialization
- ✅ Same error handling pattern (try/catch)
- ✅ Same logging pattern (console.log/error)
- ✅ Same structure (main function, async/await)

### Defensive Justification
**Why not just document in README?**
- ❌ README documentation goes stale
- ❌ Code snippets in docs can have syntax errors
- ❌ No way to verify docs are correct
- ✅ Examples can be executed and tested

**Why not use unit tests as examples?**
- ⚠️ Unit tests mock dependencies (not realistic)
- ⚠️ Unit tests test edge cases (not typical usage)
- ⚠️ Unit test syntax is test-framework specific
- ✅ Examples show real-world usage patterns

**Why examples are essential:**
- Complex workflows (OODA) have many steps
- Users learn faster from working code
- Examples catch SDK bugs (if example breaks, SDK has issues)
- Examples demonstrate best practices (error handling, logging, etc.)

---

## Decision 6: No Breaking Changes

### Context
SDK is already in use. Changes must be backward compatible.

### Decision
**All changes are strictly additive. No modifications to existing methods, parameters, or return types.**

### Engineering Logic

**Backward Compatibility Rules:**
1. ✅ **Add new methods:** `get_asset()`, `build_bom()`, etc.
2. ✅ **Add new parameters with defaults:** `kernel='rbf'`
3. ✅ **Add new TypeScript types:** Interfaces, enums
4. ❌ **Never change existing method signatures**
5. ❌ **Never remove existing methods**
6. ❌ **Never change return value structure**

**Impact Analysis:**
- **Existing users:** Continue working without changes
- **New users:** Access to full feature set
- **Documentation:** Can mark old patterns as deprecated (but keep working)
- **Migration path:** Users adopt new features at their own pace

### DRY Adherence
- ✅ **No code duplication:** New methods use same infrastructure
- ✅ **Shared validation:** New methods use existing validators
- ✅ **Shared HTTP client:** All methods use same request/response handling

### Defensive Justification
**Why not refactor as part of this work?**
```python
# TEMPTING: Refactor to "improve" architecture
def invoke_action(self, path, action, **kwargs):
    # Generic method replacing all specific methods
```
- ❌ **Breaking change:** Existing code breaks
- ❌ **Scope creep:** Mixing refactor with features
- ❌ **Risk:** Refactors introduce bugs
- ❌ **Value:** Users don't benefit from internal changes
- ✅ **Better:** Add features now, consider refactor later (separate PR)

**Why not version bump to 2.0?**
- ⚠️ Forces all users to update
- ⚠️ Fragments ecosystem (some on 1.x, some on 2.x)
- ⚠️ Documentation burden (maintain docs for two versions)
- ✅ Minor version bump (1.x → 1.y) is sufficient

**Why backward compatibility is critical:**
- SDK may be used in production systems
- Breaking changes force emergency updates
- Users lose trust in library stability
- Semantic versioning is a contract with users

---

## Decision 7: Phased Implementation

### Context
Plan includes ~500 LOC across multiple files in two languages.

### Decision
**Implement in 3 phases: Critical → Enhancement → Polish.**

### Engineering Logic

**Phase 1: Critical (Python parity)**
- **Impact:** Unblocks production use
- **Risk:** Low (following proven patterns)
- **Value:** High (completes Act phase)
- **Dependencies:** None (can ship independently)

**Phase 2: Enhancement (Interpolation convenience)**
- **Impact:** Improves developer experience
- **Risk:** Low (additive changes)
- **Value:** Medium (quality of life improvement)
- **Dependencies:** None (independent of Phase 1)

**Phase 3: Polish (Examples, docs)**
- **Impact:** Improves onboarding
- **Risk:** Very low (documentation only)
- **Value:** Medium (long-term maintenance)
- **Dependencies:** Phases 1-2 (examples use new features)

### DRY Adherence
- ✅ **Each phase is self-contained:** No code duplication between phases
- ✅ **Phases don't redo work:** Each builds on previous without modifying
- ✅ **Shared infrastructure:** All phases use same base client, validators, etc.

### Defensive Justification
**Why not implement everything at once?**
- ❌ **High risk:** Large PRs are hard to review
- ❌ **Delayed value:** Users wait longer for any improvements
- ❌ **Testing burden:** Harder to isolate failures
- ✅ **Incremental value:** Users benefit from each phase

**Why not ship each method individually?**
- ❌ **Too granular:** Overhead of 7+ separate PRs
- ❌ **Integration risk:** Methods may depend on each other
- ❌ **Documentation:** Hard to document incomplete features
- ✅ **Phase-based is balanced:** Logical groupings, manageable PRs

**Why this specific phase order?**
1. **Critical first:** Unblock users immediately
2. **Enhancement second:** Build on solid foundation
3. **Polish last:** Document proven, working features

---

## Decision 8: Follow Language Idioms

### Context
SDK supports JavaScript (promises, async/await) and Python (synchronous, type hints).

### Decision
**Follow language-specific conventions while maintaining API parity.**

### Engineering Logic

**JavaScript Idioms:**
- ✅ Async/await for all I/O operations
- ✅ Promise return types
- ✅ Destructured parameters: `{ customer_id, asset_id }`
- ✅ CamelCase method names (but matching snake_case API parameters)

**Python Idioms:**
- ✅ Type hints for all parameters and returns
- ✅ Synchronous methods (boto3 Lambda invoke is synchronous)
- ✅ Snake_case method names
- ✅ Keyword arguments with defaults

**Example of Language Parity:**
```javascript
// JavaScript: async, promises, destructured params
async buildBOM({ customer_id, asset_id, schedule_id }) {
  return this.client.post(this.endpoint, {...});
}
```

```python
# Python: sync, type hints, keyword args
def build_bom(
    self,
    customer_id: str,
    asset_id: str,
    schedule_id: Optional[str] = None
) -> Dict[str, Any]:
    return self.invoke_lambda(...)
```

### DRY Adherence
- ✅ **Same logical structure:** Method does same thing in both languages
- ✅ **Same parameter names:** `customer_id` maps 1:1 across languages
- ✅ **Same return values:** Dictionary/Object structure identical

### Defensive Justification
**Why not make them identical?**
```python
# BAD: JavaScript-style Python
async def buildBOM(self, params):
    return await self.client.post(...)
```
- ❌ Violates Python conventions (PEP 8)
- ❌ async/await adds complexity (boto3 is synchronous)
- ❌ Confuses Python developers

**Why not unify with code generation?**
- ⚠️ Adds build complexity
- ⚠️ Generated code often suboptimal
- ⚠️ Harder to debug
- ✅ Hand-written code allows language-specific optimization

**Why language idioms matter:**
- Developers have language-specific expectations
- Standard tools (linters, formatters) expect standard patterns
- Community libraries follow same patterns (consistency)
- Onboarding is easier (familiar patterns)

---

## Architectural Principles Summary

### 1. **Consistency Over Cleverness**
- Follow existing patterns, even if "better" approaches exist
- Consistency reduces cognitive load
- New developers can predict behavior

### 2. **Additive Over Destructive**
- Add features, don't change existing ones
- Deprecate gradually, never break
- Users control migration timeline

### 3. **Explicit Over Implicit**
- Named methods (`buildBOM`) over generic actions (`invoke('build', 'bom')`)
- Clear types over dynamic dispatch
- Self-documenting code over comments

### 4. **Pragmatism Over Purity**
- Convenience methods are worth the ~10 LOC each
- Examples are valuable even if they "duplicate" README content
- Type definitions are worth maintaining by hand

### 5. **User-Centric Over Engineer-Centric**
- Optimize for SDK users, not SDK maintainers
- Better DX (developer experience) justifies more code
- Discoverability trumps elegance

---

## Engineering Trade-offs Acknowledged

### Trade-off 1: Convenience Methods vs Code Volume
- **Cost:** +200 LOC for interpolation convenience methods
- **Benefit:** Better DX, type safety, discoverability
- **Decision:** Worth it (proven by existing Terminal methods)

### Trade-off 2: Examples vs Maintenance Burden
- **Cost:** Examples need updating when SDK changes
- **Benefit:** Onboarding, integration testing, documentation
- **Decision:** Worth it (examples catch bugs, help users)

### Trade-off 3: TypeScript Definitions vs Sync Burden
- **Cost:** Types must stay in sync with implementation
- **Benefit:** Compile-time safety, IDE support, refactoring confidence
- **Decision:** Worth it (TypeScript is industry standard)

### Trade-off 4: Cross-SDK Parity vs Optimization
- **Cost:** Can't optimize Python without changing JavaScript (and vice versa)
- **Benefit:** Consistent experience, shared documentation, easier migration
- **Decision:** Worth it (parity more valuable than marginal optimization)

---

## Conclusion

Every architectural decision in this plan is:
1. ✅ **Justified by engineering logic** (not arbitrary)
2. ✅ **Consistent with existing patterns** (proven in codebase)
3. ✅ **Adherent to DRY principles** (no duplication)
4. ✅ **Backward compatible** (no breaking changes)
5. ✅ **Language-appropriate** (follows idioms)
6. ✅ **User-focused** (optimizes DX over internal elegance)

The plan is conservative (low risk), incremental (phased delivery), and pragmatic (solves real user problems). All decisions prioritize long-term maintainability and user experience over short-term convenience or theoretical purity.

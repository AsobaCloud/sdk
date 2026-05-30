/**
 * TypeScript type definitions for @asoba/ona-sdk
 */

// Configuration types
export interface Credentials {
  accessKeyId: string;
  secretAccessKey: string;
  sessionToken?: string;
}

export interface Endpoints {
  forecasting?: string;
  dataIngestion?: string;
  dataStandardization?: string;
  edgeRegistry?: string;
  energyAnalyst?: string;
  enphaseHistorical?: string;
  enphaseRealTime?: string;
  huaweiHistorical?: string;
  huaweiRealTime?: string;
  globalTraining?: string;
  interpolation?: string;
  gapDetection?: string;
  terminal?: string;
  weather?: string;
  inverterTelemetry?: string;
  oodaTerminal?: string;
  partnerApi?: string;
}

export interface SDKOptions {
  region?: string;
  credentials?: Credentials;
  endpoints?: Endpoints;
  timeout?: number;
  retries?: number;
  retryDelay?: number;
  inverterTelemetryApiKey?: string;
  telemetryPollingInterval?: number;
  oodaTerminalApiKey?: string;
  oodaPollingInterval?: number;
  partnerApiKey?: string;
}

// Error types
export class OnaSDKError extends Error {
  code: string;
  details: any;
}

export class APIError extends OnaSDKError {
  statusCode: number;
  response: any;
}

export class ConfigurationError extends OnaSDKError {
  missingFields: string[];
}

export class ValidationError extends OnaSDKError {
  field: string;
  value: any;
}

export class AuthenticationError extends OnaSDKError {}

export class TimeoutError extends OnaSDKError {
  timeout: number;
}

export class RateLimitError extends OnaSDKError {}
export class ServiceUnavailableError extends OnaSDKError {}

// Telemetry types
export interface TelemetryRecord {
  asset_id: string;
  site_id: string;
  timestamp: string;
  asset_ts: string | null;
  power: number;
  kWh: number;
  kVArh: number | null;
  kVA: number | null;
  PF: number | null;
  temperature: number | null;
  inverter_state: number;
  run_state: number;
  error_code: string | null;
  error_type: string | null;
  cursor: string | null;
}

export interface TimeRange {
  start: string;
  end: string;
}

export interface CursorObject {
  asset_id: string;
  timestamp: string;
}

export interface InverterTelemetryOptions {
  asset_id?: string;
  site_id?: string;
  time_range?: TimeRange;
  resolution?: '5min' | 'daily';
  limit?: number;
  cursor?: string;
  polling_interval?: number;
}

export class InverterTelemetryClient {
  constructor(config: any);
  getInverterTelemetry(options: InverterTelemetryOptions): Promise<TelemetryRecord[]>;
  getSiteTelemetry(options: InverterTelemetryOptions): Promise<Record<string, TelemetryRecord[]>>;
  streamInverter(options: InverterTelemetryOptions): AsyncIterable<TelemetryRecord>;
  streamSite(options: InverterTelemetryOptions): AsyncIterable<TelemetryRecord>;
  getDataPeriod(options: { site_id: string; asset_id?: string }): Promise<{ site_id: string; asset_id?: string; first_record: string | null; last_record: string | null }>;
}

// OODA Terminal types
export interface OodaAlert {
  terminal_device_id: string;
  site_id: string;
  timestamp: string;
  alert_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  metadata?: Record<string, any>;
  cursor?: string;
}

export class OodaTerminalClient {
  constructor(config: any);
  getTerminalAlerts(options: { terminal_device_id: string; site_id: string; time_range: TimeRange; resolution?: string; limit?: number; cursor?: string }): Promise<OodaAlert[]>;
  getSiteAlerts(options: { site_id: string; time_range: TimeRange; resolution?: string; limit?: number }): Promise<Record<string, OodaAlert[]>>;
  getDataPeriod(options: { site_id: string; terminal_device_id?: string }): Promise<any>;
  streamTerminal(options: { terminal_device_id: string; site_id: string; cursor?: string; polling_interval?: number }): AsyncIterable<OodaAlert>;
  streamSite(options: { site_id: string; cursor?: string; polling_interval?: number }): AsyncIterable<OodaAlert>;
}

// Partner API types (Snapshots)
export interface KpiRollupSnapshot {
  site_id: string;
  period: { start: string; end: string };
  generated_at: string;
  system: {
    rated_capacity_kw: number;
    device_count: number;
  };
  energy_balance: {
    consumption_kwh: number;
    solar_production_kwh: number;
    grid_purchases_kwh: number;
    solar_offset_pct: number;
  };
  performance: {
    system_pr: number;
    pr_target: number;
    pr_status: string;
    true_uptime_pct: number;
    state_uptime_pct: number;
    availability_pct: number;
    availability_target: number;
  };
  ear: {
    energy_lost_kwh: number;
    energy_lost_pct: number;
    capacity_utilization_pct: number;
    recovery_potential_kwh: {
      "50pct": number;
      "75pct": number;
      "95pct": number;
    };
    value_lost_zar: number;
    annual_projection_zar: number;
  };
  financial: {
    tariff_currency: string;
    shortfall_cost_zar: number;
    tou_breakdown: Record<string, any>;
  };
}

export interface MaintenanceSignal {
  id: string;
  timestamp: string;
  asset_id: string;
  type: 'Critical State' | 'Warning State' | 'Temperature' | 'Capacity Underperformance' | 'Zero Production';
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  state_code?: string | null;
  rated_kw?: number | null;
  expected_kw?: number | null;
  actual_kw?: number | null;
  capacity_pct?: number | null;
  irradiance_wm2?: number | null;
  description: string;
}

export interface MaintenanceSignalsSnapshot {
  site_id: string;
  generated_at: string;
  cursor: string;
  signals: MaintenanceSignal[];
  summary: {
    by_type: Record<string, number>;
    by_severity: Record<string, number>;
    by_asset: Record<string, number>;
  };
}

export interface ForecastSnapshot {
  site_id: string;
  model_id: string;
  generated_at: string;
  horizon_hours: number;
  resolution: string;
  intervals: Array<{
    ts: string;
    p50_kw: number;
    p10_kw: number;
    p90_kw: number;
    revenue_zar: number;
  }>;
  totals: {
    total_kwh: number;
    total_revenue_zar: number;
  };
}

export interface MaintenanceTask {
  asset_id: string;
  task_type: 'inspection' | 'corrective_maintenance' | 'scheduled_service';
  reason: string;
  recommended_date: string;
  estimated_duration_hours?: number;
  priority: 'Critical' | 'High' | 'Medium' | 'Low';
}

export interface MaintenanceScheduleSnapshot {
  site_id: string;
  generated_at: string;
  horizon: { start: string; end: string };
  tasks: MaintenanceTask[];
  summary: {
    total_tasks: number;
    by_priority: Record<string, number>;
    by_task_type: Record<string, number>;
    by_asset: Record<string, number>;
  };
}

export class PartnerApiClient {
  constructor(httpClient: any, config: any);
  getKpiRollup(params: { site_id: string }): Promise<KpiRollupSnapshot>;
  getMaintenanceSignals(params: { site_id: string; since?: string; severity?: string }): Promise<MaintenanceSignalsSnapshot>;
  getForecastSnapshot(params: { site_id: string; horizon?: string }): Promise<ForecastSnapshot>;
  getMaintenanceSchedule(params: { site_id: string; since?: string }): Promise<MaintenanceScheduleSnapshot>;
  getSnapshot(params: { site_id: string; kind: string; [key: string]: any }): Promise<any>;
}

// Forecasting types
export interface DeviceForecastParams {
  site_id: string;
  device_id: string;
  forecast_hours?: number;
}

export interface SiteForecastParams {
  site_id: string;
  forecast_hours?: number;
  include_device_breakdown?: boolean;
}

export interface CustomerForecastParams {
  customer_id: string;
  forecast_hours?: number;
  capacity_kw?: number;
  manufacturer?: string;
}

export interface ForecastResult {
  customer_id?: string;
  site_id?: string;
  device_id?: string;
  forecast_hours: number;
  generated_at: string;
  forecasts: Array<{
    timestamp: string;
    hour_ahead: number;
    kWh_forecast: number;
    weather?: {
      temp?: number;
      cloudcover?: number;
      solarradiation?: number;
      conditions?: string;
    };
  }>;
  model_info: {
    model_type: string;
    optimization_strategy?: string;
    model_timestamp?: string;
    customer_validation_loss?: number;
  };
}

// Terminal API types
export interface Asset {
  customer_id: string;
  asset_id: string;
  name: string;
  type: string;
  capacity_kw: number;
  location: string;
  timezone?: string;
}

export interface AddAssetParams {
  customer_id: string;
  asset_id: string;
  name: string;
  type: string;
  capacity_kw: number;
  location: string;
  timezone?: string;
  components?: any[];
}

export interface DetectionParams {
  customer_id: string;
  asset_id: string;
  lookback_hours?: number;
}

export interface DiagnosticParams {
  customer_id: string;
  asset_id: string;
  detection_id: string;
  lookback_hours?: number;
}

export interface NowcastParams {
  customer_id: string;
  time_range?: '1h' | '6h' | '24h' | '7d' | 'latest';
  asset_filter?: string[];
}

// Energy Analyst types
export interface QueryParams {
  question: string;
  n_results?: number;
  max_new_tokens?: number;
  temperature?: number;
}

export interface QueryResponse {
  answer: string;
  sources: string[];
  citation: string;
  model_id: string;
}

export interface AddDocumentsParams {
  texts: string[];
  metadatas?: Array<Record<string, any>>;
}

export interface CollectionInfo {
  name: string;
  count: number;
  metadata: Record<string, any>;
  storage_mb: number;
  storage_gb: number;
}

// Edge Device Registry types
export interface DiscoverDeviceParams {
  ip: string;
  username: string;
}

export interface Device {
  id: string;
  ip: string;
  username: string;
  name: string;
  type: 'unknown' | 'full-platform' | 'docker-ready' | 'legacy-edge' | 'basic-edge';
  status: 'discovering' | 'online' | 'offline';
  capabilities: {
    system?: {
      available: boolean;
      service?: string;
      version?: string;
      timestamp?: string;
    };
    docker?: {
      installed: boolean;
      version?: string | null;
      containers?: any[];
    };
    platformEdge?: {
      deployed: boolean;
      version?: string | null;
      services?: any[];
    };
    services?: Array<{
      name: string;
      status: string;
      port: number;
    }>;
  };
  lastSeen: string;
  createdAt: string;
}

// Gap Detection types
export interface GapDetectionParams {
  customer_id: string;
  client_id?: string;
  region?: string;
  location?: string;
  manufacturer?: string;
  lookback_days?: number;
  min_gap_minutes?: number;
}

export interface GapDetectionResult {
  customer_id: string;
  scan_period: { start: string; end: string };
  gaps_found: Array<{
    asset_id: string;
    gap_start: string;
    gap_end: string;
    missing_intervals: number;
  }>;
  dates_needing_backfill: string[];
  backfill_targets?: Record<string, string[]>;
  total_missing_intervals: number;
  needs_backfill: boolean;
}

// Global Training types
export interface TrainRequest {
  customer_id: string;
  force?: boolean;
  promote?: boolean;
  test_only?: boolean;
}

export interface TrainingStatusResponse {
  customer_id: string;
  status: 'NOT_STARTED' | 'RUNNING' | 'SUCCEEDED' | 'FAILED';
  processing_job_name: string | null;
  last_updated: string | null;
  training_job_name?: string | null;
  processing_progress?: {
    elapsed_seconds: number;
    estimated_total_seconds: number;
    estimated_percent: number;
  } | null;
  training_progress?: {
    secondary_status: 'Starting' | 'Downloading' | 'Training' | 'Uploading' | 'Completed';
    elapsed_seconds: number;
  } | null;
}

export interface TrainResponseBatch {
  message: string;
  jobs_started: number;
  jobs_failed: number;
  jobs_skipped: number;
  total_requested: number;
  jobs: Array<{ customer_id: string; processing_job_name: string }>;
  failures?: Array<{ customer_id: string; error: string; error_code: string }> | null;
  skipped?: Array<{ customer_id: string; reason: string; processing_job_name: string }> | null;
  note: string;
}

// Service client classes
export class ForecastingClient {
  getDeviceForecast(params: DeviceForecastParams): Promise<ForecastResult>;
  getSiteForecast(params: SiteForecastParams): Promise<ForecastResult>;
  getCustomerForecast(params: CustomerForecastParams): Promise<ForecastResult>;
}

export class TerminalClient {
  listAssets(params: { customer_id: string }): Promise<{ assets: Asset[] }>;
  addAsset(params: AddAssetParams): Promise<any>;
  getAsset(params: { customer_id: string; asset_id: string }): Promise<Asset>;
  runDetection(params: DetectionParams): Promise<any>;
  listDetections(params: { customer_id: string }): Promise<any>;
  runDiagnostics(params: DiagnosticParams): Promise<any>;
  listDiagnostics(params: { customer_id: string }): Promise<any>;
  createSchedule(params: any): Promise<any>;
  listSchedules(params: { customer_id: string }): Promise<any>;
  buildBOM(params: any): Promise<any>;
  listBOMs(params: { customer_id: string }): Promise<any>;
  createOrder(params: any): Promise<any>;
  listOrders(params: { customer_id: string }): Promise<any>;
  subscribeTracking(params: { customer_id: string; job_id: string }): Promise<any>;
  listTracking(params: { customer_id: string }): Promise<any>;
  listActivities(params: { customer_id: string }): Promise<any>;
  listIssues(params: { customer_id: string }): Promise<any>;
  createIssue(params: any): Promise<any>;
  getNowcastData(params: NowcastParams): Promise<any>;
  getForecastResults(params: { customer_id: string }): Promise<any>;
  getInterpolationResults(params: { customer_id: string }): Promise<any>;
  getMLModels(): Promise<any>;
  getMLOODA(params: { customer_id: string }): Promise<any>;
}

export class EnergyAnalystClient {
  query(params: QueryParams): Promise<QueryResponse>;
  addDocuments(params: AddDocumentsParams): Promise<any>;
  uploadPDFs(files: File[]): Promise<any>;
  getCollectionInfo(): Promise<CollectionInfo>;
  clearCollection(): Promise<any>;
  getHealth(): Promise<any>;
}

export class EdgeDeviceRegistryClient {
  getDevices(): Promise<Device[]>;
  getDevice(deviceId: string): Promise<Device>;
  discoverDevice(params: DiscoverDeviceParams): Promise<Device>;
  updateDevice(deviceId: string, updates: any): Promise<Device>;
  deleteDevice(deviceId: string): Promise<any>;
  getDeviceCapabilities(deviceId: string): Promise<any>;
  getDeviceServices(deviceId: string): Promise<any>;
  getHealth(): Promise<any>;
}

export class GapDetectionClient {
  detectGaps(params: GapDetectionParams): Promise<GapDetectionResult>;
}

export class GlobalTrainingClient {
  triggerTraining(params: TrainRequest): Promise<TrainResponseBatch>;
  getTrainingStatus(customerId: string): Promise<TrainingStatusResponse>;
}

export class DataIngestionClient {
  ingest(payload: any): Promise<any>;
}

export class InterpolationClient {
  interpolate(payload: any): Promise<any>;
  splineInterpolation(params: { customer_id: string; dataset_key: string; spline_type?: string }): Promise<any>;
  gaussianProcessInterpolation(params: { customer_id: string; dataset_key: string; kernel?: string }): Promise<any>;
  physicsBasedInterpolation(params: { customer_id: string; dataset_key: string }): Promise<any>;
}

export class WeatherClient {
  updateCache(payload: any): Promise<any>;
}

export class EnphaseClient {
  getHistoricalData(payload: any): Promise<any>;
  getRealTimeData(payload: any): Promise<any>;
}

export class HuaweiClient {
  getHistoricalData(payload: any): Promise<any>;
  getRealTimeData(payload: any): Promise<any>;
}

// Main SDK class
export class OnaSDK {
  constructor(options?: SDKOptions);

  forecasting: ForecastingClient;
  terminal: TerminalClient;
  energyAnalyst: EnergyAnalystClient;
  edgeRegistry: EdgeDeviceRegistryClient;
  gapDetection: GapDetectionClient;
  globalTraining: GlobalTrainingClient;
  dataIngestion: DataIngestionClient;
  interpolation: InterpolationClient;
  weather: WeatherClient;
  enphase: EnphaseClient;
  huawei: HuaweiClient;
  inverterTelemetry: InverterTelemetryClient | null;
  oodaTerminal: OodaTerminalClient | null;
  freemiumForecast: any;
  partnerApi: PartnerApiClient | null;

  setEndpoint(serviceName: string, endpoint: string): void;
  getConfig(): any;
  static getVersion(): string;
}

// Validators
export function validateRequired(obj: any, requiredFields: string[]): void;
export function validateString(value: any, fieldName: string): void;
export function validateNumber(value: any, fieldName: string): void;
export function validatePositiveNumber(value: any, fieldName: string): void;
export function validateRange(value: number, fieldName: string, min: number, max: number): void;
export function validateArray(value: any, fieldName: string): void;
export function validateEnum(value: any, fieldName: string, allowedValues: any[]): void;
export function validateCustomerId(customerId: string): void;
export function validateSiteId(siteId: string): void;
export function validateDeviceId(deviceId: string): void;
export function validateAssetId(assetId: string): void;

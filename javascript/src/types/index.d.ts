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
  terminal?: string;
  weather?: string;
}

export interface SDKOptions {
  region?: string;
  credentials?: Credentials;
  endpoints?: Endpoints;
  timeout?: number;
  retries?: number;
  retryDelay?: number;
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
}

export interface ForecastResult {
  forecasts: Array<{
    timestamp: string;
    hour_ahead: number;
    kWh_forecast?: number;
    kVArh_forecast?: number;
    kVA_forecast?: number;
    PF_forecast?: number;
  }>;
  model_info: {
    model_type: string;
    training_level?: string;
    aggregation_method?: string;
  };
  generated_at: string;
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

export interface CleaningEvent {
  timestamp: string;
  jump_pct: number;
  pr_before: number;
  pr_after: number;
}

export interface SoilingAudit {
  soiling_rate_pct_day: number;
  detected_cleaning_events: CleaningEvent[];
  recovery_gain_kwh_last_event: number;
}

export interface Prognostics {
  battery_rul_days: number | null;
  battery_retirement_date: string | null;
  pv_annual_degradation_pct: number;
  health_score: number;
}

export interface BatteryKPIs {
  avg_soc: number | null;
  avg_soh: number | null;
  min_soh: number | null;
  max_soh: number | null;
  total_capacity_kwh: number;
  warranty_status: string;
  throughput_kwh: number;
  warranty_remaining_pct: number | null;
  cycle_count_estimate: number;
  dod_avg: number | null;
  asset_count: number;
}

export interface SiteSummary {
  total_kWh_today: number;
  fleet_availability_pct: number;
  fleet_pr_pct: number;
  active_inverters: number;
  total_inverters: number;
  last_updated: string;
  battery?: BatteryKPIs;
  soiling?: SoilingAudit;
  prognostics?: Prognostics;
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
  type: string;
  status: string;
  capabilities: Record<string, any>;
  lastSeen: string;
  createdAt: string;
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
  getSiteSummary(params: { site_id: string }): Promise<SiteSummary>;
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

export class DataIngestionClient {
  ingest(payload: any): Promise<any>;
}

export class InterpolationClient {
  interpolate(payload: any): Promise<any>;
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
  dataIngestion: DataIngestionClient;
  interpolation: InterpolationClient;
  weather: WeatherClient;
  enphase: EnphaseClient;
  huawei: HuaweiClient;

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

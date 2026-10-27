export const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

export type ModuleId = 'safety' | 'cracks' | 'valuation' | 'planning' | 'daily_assistance' | 'knowledge'
export type RiskLevel = 'Low' | 'Moderate' | 'High' | 'Critical' | 'Informational'

export interface Finding {
  label: string
  severity: string
  detail: string
}

export interface AnalysisResult {
  id: string
  module: ModuleId
  module_label: string
  title: string
  summary: string
  risk_level: RiskLevel
  findings: Finding[]
  recommendations: string[]
  assumptions: string[]
  disclaimer: string
  provider: 'demo' | 'gemini' | string
  provider_error?: string | null
  created_at: string
  project_name: string
  location: string
  image_name: string
}

export interface HealthStatus {
  status: string
  ai_enabled: boolean
  ai_provider: string
  model: string
  modules: { id: ModuleId; label: string; description: string }[]
}

export interface WeatherResult {
  location: string
  temperature_c: number | null
  feels_like_c: number | null
  humidity_percent: number | null
  wind_kmh: number | null
  wind_gust_kmh: number | null
  precipitation_mm: number | null
  condition: string
  precipitation_probability_max: number | null
  advisory: string[]
  source: string
  observed_at: string
}

async function readError(response: Response): Promise<never> {
  let message = `Request failed (${response.status})`
  try {
    const body = await response.json()
    if (typeof body.detail === 'string') message = body.detail
  } catch {
    // Keep the HTTP status message when the response isn't JSON.
  }
  throw new Error(message)
}

export async function getHealth(): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE}/health`)
  if (!response.ok) return readError(response)
  return response.json()
}

export async function getDashboard() {
  const response = await fetch(`${API_BASE}/dashboard`)
  if (!response.ok) return readError(response)
  return response.json() as Promise<{ total_analyses: number; high_risk_reports: number; analyses_last_7_days: number; recent_analyses: AnalysisResult[]; modules: number }>
}

export async function getAnalyses(): Promise<AnalysisResult[]> {
  const response = await fetch(`${API_BASE}/analyses?limit=40`)
  if (!response.ok) return readError(response)
  const body = await response.json()
  return body.items as AnalysisResult[]
}

export async function createAnalysis(values: {
  module: ModuleId
  prompt: string
  project_name: string
  location: string
  property_type: string
  area_sqft: string
  market_rate_sqft: string
  budget: string
  timeline: string
  file?: File | null
}): Promise<AnalysisResult> {
  const form = new FormData()
  Object.entries(values).forEach(([key, value]) => {
    if (key === 'file') {
      if (value instanceof File) form.append('file', value)
    } else if (value !== undefined && value !== null) form.append(key, String(value))
  })
  const response = await fetch(`${API_BASE}/analyze`, { method: 'POST', body: form })
  if (!response.ok) return readError(response)
  return response.json()
}

export async function getWeather(location: string): Promise<WeatherResult> {
  const response = await fetch(`${API_BASE}/weather?location=${encodeURIComponent(location)}`)
  if (!response.ok) return readError(response)
  return response.json()
}

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import {
  Activity, AlertTriangle, ArrowRight, ArrowUpRight, Bell, Building2,
  CalendarDays, Check, ChevronDown, CircleHelp, CloudRain, CloudSun, FileImage, FileText,
  History, House, Layers3, LoaderCircle, Menu, MessageSquareText,
  Plus, Search, ShieldCheck, Sparkles, UploadCloud, Wind, X, Zap,
} from 'lucide-react'
import {
  AnalysisResult, HealthStatus, ModuleId, WeatherResult, createAnalysis, getAnalyses,
  getDashboard, getHealth, getWeather,
} from './api'

type View = 'overview' | 'analysis' | 'history'

type ModuleInfo = {
  id: ModuleId
  name: string
  description: string
  icon: typeof ShieldCheck
  tint: string
  category: string
}

const MODULES: ModuleInfo[] = [
  { id: 'safety', name: 'Site safety monitoring', description: 'Identify visible risks, PPE gaps, and safer next steps.', icon: ShieldCheck, tint: 'mint', category: 'Vision analysis' },
  { id: 'cracks', name: 'Structural crack analysis', description: 'Document visible crack patterns and escalation checks.', icon: Activity, tint: 'rose', category: 'Vision analysis' },
  { id: 'valuation', name: 'Real estate valuation', description: 'Build a transparent property valuation framework.', icon: House, tint: 'blue', category: 'Planning intelligence' },
  { id: 'planning', name: 'Project planning', description: 'Organise phases, dependencies, milestones, and risks.', icon: Layers3, tint: 'violet', category: 'Planning intelligence' },
  { id: 'daily_assistance', name: 'Daily site assistant', description: 'Get practical guidance for an issue on site.', icon: MessageSquareText, tint: 'amber', category: 'Site copilot' },
  { id: 'knowledge', name: 'Construction knowledge', description: 'Understand construction workflows and documentation.', icon: CircleHelp, tint: 'slate', category: 'Site copilot' },
]

const PROMPT_PLACEHOLDERS: Record<ModuleId, string> = {
  safety: 'Describe the site activity, suspected hazard, or area to inspect…',
  cracks: 'Where is the crack? When was it first noticed? Has it changed or appeared with other symptoms?',
  valuation: 'Add details like age, condition, floor, frontage, amenities, nearby comparable rates, or your valuation goal…',
  planning: 'Describe the project type, current stage, scope, constraints, and target completion date…',
  daily_assistance: 'What is happening on site today? Include the activity, materials, drawing reference, and constraint…',
  knowledge: 'Ask a construction concept, documentation, sequencing, quality, or safety question…',
}

const STARTER_PROMPTS: Record<ModuleId, string> = {
  safety: 'Review the visible safety risks and prepare a short site inspection checklist.',
  cracks: 'Help me document this crack and decide what signs need urgent professional review.',
  valuation: 'Help me structure an indicative property valuation and list missing inputs.',
  planning: 'Create an initial sequence with milestones, dependencies, inspections, and risks.',
  daily_assistance: 'Help me decide the safest practical next steps for this site issue.',
  knowledge: 'Explain the process step by step and list key quality and safety checks.',
}

function formatDate(value?: string) {
  if (!value) return 'Just now'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }).format(date)
}

function riskClass(risk?: string) {
  const key = (risk || 'informational').toLowerCase()
  if (key === 'critical') return 'risk-critical'
  if (key === 'high') return 'risk-high'
  if (key === 'moderate' || key === 'medium') return 'risk-moderate'
  if (key === 'low') return 'risk-low'
  return 'risk-info'
}

function App() {
  const [view, setView] = useState<View>('overview')
  const [activeModule, setActiveModule] = useState<ModuleId>('safety')
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [analyses, setAnalyses] = useState<AnalysisResult[]>([])
  const [stats, setStats] = useState({ total_analyses: 0, high_risk_reports: 0, analyses_last_7_days: 0 })
  const [loadingPage, setLoadingPage] = useState(true)
  const [backendError, setBackendError] = useState('')
  const [searchText, setSearchText] = useState('')
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [projectName, setProjectName] = useState('Indore Residential Project')
  const [location, setLocation] = useState('Indore, Madhya Pradesh')
  const [propertyType, setPropertyType] = useState('Residential building')
  const [areaSqft, setAreaSqft] = useState('1800')
  const [marketRateSqft, setMarketRateSqft] = useState('')
  const [budget, setBudget] = useState('₹45 lakh')
  const [timeline, setTimeline] = useState('6 months')
  const [prompt, setPrompt] = useState(STARTER_PROMPTS.safety)
  const [file, setFile] = useState<File | null>(null)
  const [dragging, setDragging] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [weatherLocation, setWeatherLocation] = useState('Indore')
  const [weather, setWeather] = useState<WeatherResult | null>(null)
  const [weatherLoading, setWeatherLoading] = useState(false)
  const [weatherError, setWeatherError] = useState('')
  const uploadRef = useRef<HTMLInputElement>(null)

  const selectedModule = useMemo(() => MODULES.find(item => item.id === activeModule) || MODULES[0], [activeModule])

  const refreshData = useCallback(async () => {
    setLoadingPage(true)
    setBackendError('')
    try {
      const [healthData, dashboardData, history] = await Promise.all([getHealth(), getDashboard(), getAnalyses()])
      setHealth(healthData)
      setStats({ total_analyses: dashboardData.total_analyses, high_risk_reports: dashboardData.high_risk_reports, analyses_last_7_days: dashboardData.analyses_last_7_days })
      setAnalyses(history)
    } catch (err) {
      setBackendError(err instanceof Error ? err.message : 'Cannot connect to the API.')
    } finally {
      setLoadingPage(false)
    }
  }, [])

  useEffect(() => { void refreshData() }, [refreshData])

  const chooseModule = (module: ModuleId) => {
    setActiveModule(module)
    setPrompt(STARTER_PROMPTS[module])
    setResult(null)
    setError('')
    setView('analysis')
    setMobileNavOpen(false)
  }

  const runAnalysis = async (event: FormEvent) => {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    setResult(null)
    try {
      const created = await createAnalysis({ module: activeModule, prompt, project_name: projectName, location, property_type: propertyType, area_sqft: areaSqft, market_rate_sqft: marketRateSqft, budget, timeline, file })
      setResult(created)
      await refreshData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'The analysis could not be completed.')
    } finally {
      setSubmitting(false)
    }
  }

  const runWeather = async (event: FormEvent) => {
    event.preventDefault()
    setWeatherLoading(true)
    setWeatherError('')
    try {
      setWeather(await getWeather(weatherLocation))
    } catch (err) {
      setWeatherError(err instanceof Error ? err.message : 'Weather could not be loaded.')
    } finally {
      setWeatherLoading(false)
    }
  }

  const filteredHistory = analyses.filter(item => `${item.title} ${item.module_label} ${item.project_name} ${item.location}`.toLowerCase().includes(searchText.toLowerCase()))

  const nav = (
    <>
      <div className="brand">
        <div className="brand-mark"><Building2 size={23} strokeWidth={2.2} /></div>
        <div><div className="brand-name">Build<span>Intel</span></div><div className="brand-caption">CONSTRUCTION AI</div></div>
      </div>
      <div className="workspace-switch"><div className="workspace-avatar">IP</div><div className="workspace-copy"><strong>Indore Projects</strong><span>Team workspace</span></div><ChevronDown size={15} /></div>
      <div className="nav-label">WORKSPACE</div>
      <button className={`nav-item ${view === 'overview' ? 'active' : ''}`} onClick={() => { setView('overview'); setMobileNavOpen(false) }}><Layers3 size={18} /> Overview</button>
      <button className={`nav-item ${view === 'analysis' ? 'active' : ''}`} onClick={() => { setView('analysis'); setMobileNavOpen(false) }}><Sparkles size={18} /> New analysis <span className="nav-plus"><Plus size={14} /></span></button>
      <button className={`nav-item ${view === 'history' ? 'active' : ''}`} onClick={() => { setView('history'); setMobileNavOpen(false) }}><History size={18} /> Analysis history</button>
      <div className="nav-label nav-spaced">AI MODULES</div>
      {MODULES.map(module => {
        const Icon = module.icon
        return <button key={module.id} className={`nav-item nav-module ${view === 'analysis' && activeModule === module.id ? 'active' : ''}`} onClick={() => chooseModule(module.id)}><Icon size={17} /><span>{module.name}</span></button>
      })}
      <div className="sidebar-bottom">
        <div className="help-card"><div className="help-icon"><CircleHelp size={18} /></div><strong>Need a hand?</strong><p>Learn how to get reliable results from your site data.</p><button onClick={() => chooseModule('knowledge')}>Ask the assistant <ArrowRight size={14} /></button></div>
        <div className="user-row"><div className="user-avatar">DS</div><div className="user-copy"><strong>Dev Sharma</strong><span>Project owner</span></div><button className="icon-button small" aria-label="Open profile"><ChevronDown size={16} /></button></div>
      </div>
    </>
  )

  return (
    <div className="app-shell">
      {mobileNavOpen && <button className="mobile-scrim" aria-label="Close menu" onClick={() => setMobileNavOpen(false)} />}
      <aside className={`sidebar ${mobileNavOpen ? 'sidebar-open' : ''}`}>{nav}</aside>
      <main className="main-area">
        <header className="topbar">
          <div className="topbar-left"><button className="mobile-menu icon-button" onClick={() => setMobileNavOpen(true)} aria-label="Open menu"><Menu size={20} /></button><div className="breadcrumbs"><span>Workspace</span><span className="crumb-slash">/</span><strong>{view === 'overview' ? 'Overview' : view === 'history' ? 'Analysis history' : 'New analysis'}</strong></div></div>
          <div className="topbar-actions"><div className={`connection-pill ${health?.ai_enabled ? 'connected' : 'demo'}`}><span className="status-dot" />{health?.ai_enabled ? 'Gemini connected' : 'Demo mode'}</div><button className="icon-button notification-button" aria-label="Notifications"><Bell size={18} /><i /></button><div className="topbar-avatar">DS</div></div>
        </header>
        {backendError && <div className="backend-alert"><AlertTriangle size={18} /><div><strong>Backend connection needed</strong><span>{backendError}. Start the FastAPI server as described in README.md.</span></div><button onClick={() => void refreshData()}>Retry</button></div>}
        {view === 'overview' && <section className="page-content">
          <div className="welcome-row"><div><div className="eyebrow"><span className="eyebrow-line" /> SMARTER SITE DECISIONS</div><h1>Construction intelligence,<br className="desktop-break" /> all in one place.</h1><p className="page-subtitle">Turn site photos, project details, and daily questions into clearer next steps.</p></div><button className="primary-button" onClick={() => chooseModule('safety')}><Plus size={17} /> Start new analysis</button></div>
          <div className="metric-grid">
            <MetricCard icon={<FileText size={19} />} label="Total analyses" value={String(stats.total_analyses)} helper="Saved to your workspace" tone="blue" trend={<Layers3 size={15} />} />
            <MetricCard icon={<AlertTriangle size={19} />} label="Higher-risk reports" value={String(stats.high_risk_reports)} helper="Reports flagged High / Critical" tone="orange" trend={<ArrowUpRight size={15} />} />
            <MetricCard icon={<CalendarDays size={19} />} label="Last 7 days" value={String(stats.analyses_last_7_days)} helper="Recent analysis activity" tone="purple" trend={<Activity size={15} />} />
            <MetricCard icon={<Zap size={19} />} label="AI availability" value={health?.ai_enabled ? 'Connected' : 'Demo'} helper={health?.ai_enabled ? (health.model || 'Gemini model ready') : 'Add a Gemini key to enable AI'} tone="green" trend={<Sparkles size={15} />} />
          </div>
          <div className="section-heading"><div><h2>Choose an intelligence module</h2><p>Start with the question you need to solve today.</p></div><button className="text-button" onClick={() => setView('analysis')}>Explore all <ArrowRight size={15} /></button></div>
          <div className="module-grid">
            {MODULES.map(module => {
              const Icon = module.icon
              return <button key={module.id} className="module-card" onClick={() => chooseModule(module.id)}><div className={`module-icon ${module.tint}`}><Icon size={21} /></div><div className="module-category">{module.category}</div><h3>{module.name}</h3><p>{module.description}</p><div className="card-bottom"><span>Open module</span><span className="arrow-circle"><ArrowUpRight size={16} /></span></div></button>
            })}
          </div>
          <div className="lower-grid">
            <section className="panel recent-panel"><div className="panel-header"><div><h2>Recent analyses</h2><p>Your latest site intelligence reports</p></div><button className="text-button" onClick={() => setView('history')}>View history <ArrowRight size={15} /></button></div>
              {analyses.length ? <div className="recent-list">{analyses.slice(0, 4).map(item => <AnalysisRow key={item.id} item={item} onClick={() => { setResult(item); setActiveModule(item.module); setView('analysis') }} />)}</div> : <EmptyState icon={<FileText size={21} />} title="No analyses yet" text="Your generated reports will appear here." action={() => chooseModule('safety')} actionLabel="Create first report" />}
            </section>
            <section className="panel weather-panel"><div className="panel-header"><div><h2>Site weather</h2><p>Conditions that may affect work today</p></div><div className="weather-cloud-icon"><CloudSun size={22} /></div></div>
              <form className="weather-search" onSubmit={runWeather}><div className="search-input-wrap"><Search size={16} /><input value={weatherLocation} onChange={event => setWeatherLocation(event.target.value)} placeholder="Enter city or area" aria-label="Weather location" /></div><button type="submit" aria-label="Get weather" disabled={weatherLoading}>{weatherLoading ? <LoaderCircle className="spin" size={16} /> : <ArrowRight size={16} />}</button></form>
              {weatherError && <div className="inline-error">{weatherError}</div>}
              {weather ? <><div className="weather-current"><div><div className="weather-place">{weather.location}</div><div className="weather-temp">{weather.temperature_c ?? '—'}°<span>C</span></div><div className="weather-condition">{weather.condition}</div></div><div className="weather-symbol"><CloudSun size={42} /></div></div><div className="weather-facts"><WeatherFact label="Humidity" value={weather.humidity_percent == null ? '—' : `${weather.humidity_percent}%`} /><WeatherFact label="Wind" value={weather.wind_kmh == null ? '—' : `${weather.wind_kmh} km/h`} /><WeatherFact label="Rain" value={weather.precipitation_mm == null ? '—' : `${weather.precipitation_mm} mm`} /></div><div className="advisory-box"><div><Wind size={15} /> Site advisory</div>{weather.advisory[0]}</div><div className="weather-source">Source: {weather.source} · {weather.observed_at || 'Current conditions'}</div></> : <div className="weather-empty"><div className="weather-empty-icon"><CloudRain size={23} /></div><strong>Plan around the weather</strong><p>Search a city to see current conditions and a simple site advisory.</p><div className="weather-prompt" onClick={() => setWeatherLocation(location.split(',')[0] || 'Indore')}>Use project location <ArrowRight size={13} /></div></div>}
            </section>
          </div>
          <div className="disclaimer-strip"><ShieldCheck size={17} /><span><strong>Built for informed decisions.</strong> AI output is assistive, not a substitute for qualified safety, structural, engineering, or valuation review.</span><button onClick={() => chooseModule('knowledge')}>Read guidance <ArrowRight size={14} /></button></div>
        </section>}

        {view === 'analysis' && <section className="page-content analysis-page">
          <div className="page-title-row"><div><div className="eyebrow"><span className="eyebrow-line" /> WORKSPACE / ANALYSIS</div><h1>{result ? 'Analysis report' : 'New analysis'}</h1><p className="page-subtitle">{result ? 'Review findings and recommended actions from your latest run.' : 'Add the context you have. You can run a text-only analysis or attach a site image.'}</p></div><button className="secondary-button" onClick={() => { setResult(null); setView('history') }}><History size={16} /> View history</button></div>
          {!result ? <div className="analysis-layout"><form className="panel analysis-form" onSubmit={runAnalysis}>
            <div className="form-section-heading"><div className={`module-icon ${selectedModule.tint}`}><selectedModule.icon size={20} /></div><div><h2>{selectedModule.name}</h2><p>{selectedModule.description}</p></div><span className="step-badge">01</span></div>
            <label className="field-label">Analysis type</label><div className="module-select-grid">{MODULES.map(module => <button type="button" key={module.id} className={`module-select ${activeModule === module.id ? 'selected' : ''}`} onClick={() => { setActiveModule(module.id); setPrompt(STARTER_PROMPTS[module.id]); setFile(null) }}><module.icon size={17} /><span>{module.name}</span>{activeModule === module.id && <Check size={15} />}</button>)}</div>
            <div className="form-divider" />
            <div className="field-grid"><label className="field-wrap"><span className="field-label">Project name</span><input value={projectName} onChange={event => setProjectName(event.target.value)} maxLength={120} placeholder="e.g. Residential tower" /></label><label className="field-wrap"><span className="field-label">Site location</span><input value={location} onChange={event => setLocation(event.target.value)} maxLength={160} placeholder="City, state" /></label></div>
            {activeModule === 'valuation' && <div className="field-grid"><label className="field-wrap"><span className="field-label">Property type</span><select value={propertyType} onChange={event => setPropertyType(event.target.value)}><option>Residential building</option><option>Apartment</option><option>Commercial property</option><option>Plot / land</option><option>Industrial property</option><option>Other</option></select></label><label className="field-wrap"><span className="field-label">Built-up / plot area (sq ft)</span><input value={areaSqft} onChange={event => setAreaSqft(event.target.value)} placeholder="e.g. 1800" /></label><label className="field-wrap"><span className="field-label">Local rate per sq ft (₹) <span className="optional-text">Optional</span></span><input value={marketRateSqft} onChange={event => setMarketRateSqft(event.target.value)} placeholder="e.g. 5500" /></label><label className="field-wrap"><span className="field-label">Known budget / asking price</span><input value={budget} onChange={event => setBudget(event.target.value)} placeholder="Optional" /></label></div>}
            {activeModule === 'planning' && <div className="field-grid"><label className="field-wrap"><span className="field-label">Target timeline</span><input value={timeline} onChange={event => setTimeline(event.target.value)} placeholder="e.g. 6 months" /></label><label className="field-wrap"><span className="field-label">Budget context</span><input value={budget} onChange={event => setBudget(event.target.value)} placeholder="Optional" /></label></div>}
            <label className="field-wrap prompt-wrap"><span className="field-label">Question / site context <span className="optional-text">Recommended</span></span><textarea value={prompt} onChange={event => setPrompt(event.target.value)} maxLength={8000} rows={5} placeholder={PROMPT_PLACEHOLDERS[activeModule]} /><span className="field-hint">Add measurements, symptoms, current stage, constraints, and what you need to decide.</span></label>
            {(activeModule === 'safety' || activeModule === 'cracks') && <div className={`upload-zone ${dragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`} onDragOver={event => { event.preventDefault(); setDragging(true) }} onDragLeave={() => setDragging(false)} onDrop={event => { event.preventDefault(); setDragging(false); const dropped = event.dataTransfer.files[0]; if (dropped) { if (['image/jpeg', 'image/png', 'image/webp'].includes(dropped.type)) setFile(dropped); else setError('Choose a JPG, PNG, or WebP image.') } }}><input ref={uploadRef} type="file" accept="image/png,image/jpeg,image/webp" hidden onChange={event => { const selected = event.target.files?.[0]; if (selected && selected.size <= 10 * 1024 * 1024) { setFile(selected); setError('') } else if (selected) setError('Choose an image smaller than 10 MB.') }} />{file ? <><div className="upload-icon done"><FileImage size={22} /></div><div className="upload-copy"><strong>{file.name}</strong><span>{(file.size / 1024 / 1024).toFixed(2)} MB · Ready for analysis</span></div><button type="button" className="remove-file" onClick={() => { setFile(null); if (uploadRef.current) uploadRef.current.value = '' }} aria-label="Remove file"><X size={17} /></button></> : <><div className="upload-icon"><UploadCloud size={22} /></div><div className="upload-copy"><strong>Upload a site photo <span>(optional)</span></strong><span>Drag and drop, or <button type="button" className="inline-upload" onClick={() => uploadRef.current?.click()}>browse files</button></span><small>JPG, PNG or WebP · Max 10 MB · Avoid sensitive images</small></div><button type="button" className="browse-button" onClick={() => uploadRef.current?.click()}>Browse</button></>}</div>}
            <div className="privacy-note"><ShieldCheck size={15} /><span>Uploaded images are processed for this request and are not stored in the local history database.</span></div>
            {error && <div className="form-error"><AlertTriangle size={16} />{error}</div>}
            <div className="form-actions"><span className="run-note"><Sparkles size={15} />{health?.ai_enabled ? 'Gemini multimodal analysis' : 'Demo template · configure Gemini for AI results'}</span><button className="primary-button run-button" disabled={submitting || !!backendError}>{submitting ? <><LoaderCircle className="spin" size={17} /> Analysing…</> : <><Sparkles size={17} /> Generate report <ArrowRight size={16} /></>}</button></div>
          </form><aside className="analysis-aside"><div className="panel aside-card"><div className="aside-heading"><Sparkles size={18} /><h3>How to get better results</h3></div><div className="tip-list"><Tip number="01" title="Be specific" text="Include the exact area, construction stage, symptom, and when it started." /><Tip number="02" title="Add visual context" text="For image modules, include one clear image and a wider shot when possible." /><Tip number="03" title="Verify before action" text="Use suggestions as a starting point and escalate safety-critical issues." /></div></div><div className="safety-callout"><AlertTriangle size={18} /><div><strong>Safety-critical reminder</strong><p>AI can miss hazards or misread cracks. Never use this report alone to declare a structure safe or approve work.</p></div></div><div className="aside-mini"><div className="aside-mini-icon"><FileText size={17} /></div><div><strong>Reports are saved automatically</strong><span>Find previous runs under Analysis history.</span></div></div></aside></div> : <ReportView result={result} onNew={() => { setResult(null); setPrompt(STARTER_PROMPTS[activeModule]) }} />}
        </section>}

        {view === 'history' && <section className="page-content history-page"><div className="page-title-row"><div><div className="eyebrow"><span className="eyebrow-line" /> WORKSPACE / REPORTS</div><h1>Analysis history</h1><p className="page-subtitle">Browse your saved reports and reopen the details.</p></div><button className="primary-button" onClick={() => chooseModule('safety')}><Plus size={17} /> New analysis</button></div><div className="history-toolbar"><div className="history-search"><Search size={17} /><input value={searchText} onChange={event => setSearchText(event.target.value)} placeholder="Search reports, modules, locations…" /></div><span>{filteredHistory.length} report{filteredHistory.length === 1 ? '' : 's'}</span></div><div className="panel history-panel">{filteredHistory.length ? filteredHistory.map(item => <AnalysisRow key={item.id} item={item} expanded onClick={() => { setResult(item); setActiveModule(item.module); setView('analysis') }} />) : <EmptyState icon={<History size={22} />} title={searchText ? 'No matching reports' : 'Your history is empty'} text={searchText ? 'Try another search term.' : 'Run an analysis to create your first saved report.'} action={() => searchText ? setSearchText('') : chooseModule('safety')} actionLabel={searchText ? 'Clear search' : 'Start analysis'} />}</div><div className="disclaimer-strip"><ShieldCheck size={17} /><span>Reports are stored in the local SQLite database on the machine running the backend. Set up an authenticated database before a multi-user or production deployment.</span></div></section>}
        <footer className="footer"><span>© 2026 BuildIntel · Construction Intelligence Platform</span><span><span className="footer-status" /> API {backendError ? 'disconnected' : loadingPage ? 'checking' : health ? 'operational' : 'checking'} <span className="footer-divider">·</span> Built for project teams</span></footer>
      </main>
    </div>
  )
}

function MetricCard({ icon, label, value, helper, tone, trend }: { icon: ReactNode; label: string; value: string; helper: string; tone: string; trend: ReactNode }) {
  return <div className="metric-card"><div className="metric-top"><div className={`metric-icon ${tone}`}>{icon}</div><div className={`metric-trend ${tone}`}>{trend}</div></div><div className="metric-label">{label}</div><div className="metric-value">{value}</div><div className="metric-helper">{helper}</div></div>
}

function AnalysisRow({ item, onClick, expanded = false }: { item: AnalysisResult; onClick: () => void; expanded?: boolean }) {
  const module = MODULES.find(candidate => candidate.id === item.module)
  const Icon = module?.icon || FileText
  return <button className={`analysis-row ${expanded ? 'history-row' : ''}`} onClick={onClick}><div className={`row-icon ${module?.tint || 'slate'}`}><Icon size={18} /></div><div className="row-content"><strong>{item.title}</strong><span>{item.module_label || module?.name} <i /> {item.project_name || 'Untitled site project'}{item.location ? ` · ${item.location}` : ''}</span></div><span className={`risk-badge ${riskClass(item.risk_level)}`}>{item.risk_level}</span><span className="row-provider">{item.provider === 'gemini' ? 'Gemini' : 'Demo'}</span><span className="row-date">{formatDate(item.created_at)}</span><ArrowRight className="row-arrow" size={16} /></button>
}

function EmptyState({ icon, title, text, action, actionLabel }: { icon: ReactNode; title: string; text: string; action: () => void; actionLabel: string }) {
  return <div className="empty-state"><div className="empty-icon">{icon}</div><strong>{title}</strong><p>{text}</p><button className="secondary-button" onClick={action}>{actionLabel} <ArrowRight size={14} /></button></div>
}

function WeatherFact({ label, value }: { label: string; value: string }) {
  return <div className="weather-fact"><span>{label}</span><strong>{value}</strong></div>
}

function Tip({ number, title, text }: { number: string; title: string; text: string }) {
  return <div className="tip-item"><span className="tip-number">{number}</span><div><strong>{title}</strong><p>{text}</p></div></div>
}

function ReportView({ result, onNew }: { result: AnalysisResult; onNew: () => void }) {
  const [copied, setCopied] = useState(false)
  const reportText = useMemo(() => `${result.title}\n${result.summary}\n\nFindings:\n${result.findings.map(f => `- [${f.severity}] ${f.label}: ${f.detail}`).join('\n')}\n\nRecommendations:\n${result.recommendations.map(r => `- ${r}`).join('\n')}\n\nDisclaimer: ${result.disclaimer}`, [result])
  const copyReport = async () => {
    try {
      await navigator.clipboard.writeText(reportText)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1800)
    } catch {
      setCopied(false)
    }
  }
  return <div className="report-wrap"><div className="report-top-actions"><div className="result-status"><span className="result-check"><Check size={14} /></span> Report generated <span className="result-dot">·</span> {formatDate(result.created_at)}</div><div className="report-actions"><button className="secondary-button" onClick={() => void copyReport()}><FileText size={15} /> {copied ? 'Copied' : 'Copy report'}</button><button className="primary-button" onClick={onNew}><Plus size={16} /> New run</button></div></div><div className="report-hero panel"><div className="report-hero-main"><div className="report-icon"><Sparkles size={22} /></div><div><div className="report-eyebrow">{result.module_label} <span>·</span> {result.provider === 'gemini' ? 'Gemini AI' : 'Demo template'}</div><h2>{result.title}</h2><p>{result.summary}</p></div></div><div className="report-hero-meta"><div><span>Project</span><strong>{result.project_name || 'Untitled site project'}</strong></div><div><span>Location</span><strong>{result.location || 'Not specified'}</strong></div><div><span>Risk overview</span><strong><span className={`risk-badge ${riskClass(result.risk_level)}`}>{result.risk_level}</span></strong></div></div></div>{result.provider === 'demo' && <div className="demo-notice"><AlertTriangle size={16} /><span><strong>This is a demo-mode report.</strong> It is an illustrative template, not an actual AI interpretation of your input or image. Set <code>GEMINI_API_KEY</code> in <code>backend/.env</code> and restart the server for model-generated results.</span></div>}{result.provider_error && <div className="demo-notice"><AlertTriangle size={16} /><span>Gemini could not complete this run; the result fell back to demo mode. Check backend logs and API quota/settings.</span></div>}<div className="report-columns"><section className="panel report-section"><div className="panel-header"><div><h2>Findings</h2><p>{result.findings.length} observation{result.findings.length === 1 ? '' : 's'} in this report</p></div><span className="section-count">{String(result.findings.length).padStart(2, '0')}</span></div>{result.findings.length ? <div className="findings-list">{result.findings.map((finding, index) => <div className="finding-item" key={`${finding.label}-${index}`}><div className={`finding-mark ${riskClass(finding.severity)}`}><AlertTriangle size={16} /></div><div className="finding-copy"><div><strong>{finding.label}</strong><span className={`risk-badge ${riskClass(finding.severity)}`}>{finding.severity}</span></div><p>{finding.detail}</p></div></div>)}</div> : <p className="muted-paragraph">No structured findings were returned. Read the summary and recommendations carefully.</p>}</section><section className="panel report-section recommendations-section"><div className="panel-header"><div><h2>Recommended actions</h2><p>Practical next steps to consider</p></div><div className="recommendation-mark"><Check size={17} /></div></div>{result.recommendations.length ? <ol className="recommendations-list">{result.recommendations.map((recommendation, index) => <li key={`${recommendation}-${index}`}><span>{String(index + 1).padStart(2, '0')}</span><p>{recommendation}</p></li>)}</ol> : <p className="muted-paragraph">No recommendations returned.</p>}<div className="report-disclaimer"><ShieldCheck size={16} /><p>{result.disclaimer}</p></div></section></div>{result.assumptions?.length > 0 && <section className="panel assumptions-panel"><div className="panel-header"><div><h2>Assumptions & limitations</h2><p>Inputs or checks that still need verification</p></div></div><ul>{result.assumptions.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}</ul></section>}<div className="report-footer-note"><ShieldCheck size={17} /><p>For safety, structural, engineering, and financial decisions, have a qualified professional validate relevant facts and recommendations before acting.</p></div></div>
}

export default App

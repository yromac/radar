import { useState } from 'react'
import { icalFeedUrl } from '../api'
import { EventCategory, EventFilters } from '../types'
import { CategoryPill } from '../components/CategoryBadge'

const CATEGORIES: Array<EventCategory | 'all'> = [
  'all', 'arts', 'film', 'music', 'food', 'tech',
  'community', 'outdoor', 'wellness', 'sports',
]

const CALENDAR_APPS = [
  {
    name: 'Apple Calendar',
    icon: '🍎',
    steps: [
      'Open Calendar → File → New Calendar Subscription',
      'Paste the URL below',
      'Set auto-refresh to "Every Day"',
    ],
  },
  {
    name: 'Google Calendar',
    icon: '📅',
    steps: [
      'Open Google Calendar → Other Calendars → From URL',
      'Paste the URL below and click "Add Calendar"',
      'Google refreshes subscriptions every 24 hours',
    ],
  },
  {
    name: 'Outlook',
    icon: '📧',
    steps: [
      'Open Outlook → Add Calendar → Subscribe from web',
      'Paste the URL and click Import',
      'Outlook syncs every 24 hours',
    ],
  },
]

export function Subscribe() {
  const [filters, setFilters] = useState<EventFilters>({})
  const [freeOnly, setFreeOnly] = useState(false)
  const [exclusiveOnly, setExclusiveOnly] = useState(false)
  const [copied, setCopied] = useState(false)

  const activeFilters: EventFilters = {
    ...filters,
    is_free: freeOnly ? true : '',
    is_exclusive: exclusiveOnly ? true : '',
  }

  const feedUrl = icalFeedUrl(activeFilters)

  const copy = () => {
    navigator.clipboard.writeText(feedUrl).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  const setCategory = (cat: EventCategory | 'all') =>
    setFilters(f => ({ ...f, category: cat === 'all' ? '' : cat }))

  return (
    <div className="min-h-screen pt-24 pb-16 px-6">
      <div className="max-w-2xl mx-auto space-y-12">
        {/* Header */}
        <div className="space-y-3">
          <h1 className="text-3xl font-bold tracking-tight">Subscribe to Your Feed</h1>
          <p className="text-radar-muted leading-relaxed">
            Customize your feed, copy the URL, and paste it into your calendar app.
            Events will appear automatically every morning — no app to open.
          </p>
        </div>

        {/* Customize */}
        <section className="space-y-6 p-6 bg-radar-surface rounded-xl border border-radar-border">
          <h2 className="font-semibold text-sm uppercase tracking-widest text-radar-muted">
            Customize Your Feed
          </h2>

          {/* Category */}
          <div className="space-y-3">
            <p className="text-sm font-medium">Category</p>
            <div className="flex flex-wrap gap-2">
              {CATEGORIES.map(cat => (
                <CategoryPill
                  key={cat}
                  category={cat}
                  active={(cat === 'all' && !filters.category) || filters.category === cat}
                  onClick={() => setCategory(cat)}
                />
              ))}
            </div>
          </div>

          {/* Toggles */}
          <div className="flex gap-4 flex-wrap">
            <label className="flex items-center gap-2.5 cursor-pointer group">
              <Toggle checked={freeOnly} onChange={setFreeOnly} />
              <span className="text-sm group-hover:text-radar-green transition-colors">Free events only</span>
            </label>
            <label className="flex items-center gap-2.5 cursor-pointer group">
              <Toggle checked={exclusiveOnly} onChange={setExclusiveOnly} />
              <span className="text-sm group-hover:text-radar-green transition-colors">Exclusive events only</span>
            </label>
          </div>
        </section>

        {/* URL */}
        <section className="space-y-4">
          <h2 className="font-semibold text-sm uppercase tracking-widest text-radar-muted">
            Your Feed URL
          </h2>
          <div className="flex gap-2">
            <code className="flex-1 input font-mono text-xs text-radar-green break-all">
              {feedUrl}
            </code>
            <button
              onClick={copy}
              className={`shrink-0 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                copied
                  ? 'bg-radar-green text-radar-bg'
                  : 'btn-ghost'
              }`}
            >
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
        </section>

        {/* Calendar app instructions */}
        <section className="space-y-5">
          <h2 className="font-semibold text-sm uppercase tracking-widest text-radar-muted">
            Add to Your Calendar App
          </h2>
          <div className="space-y-4">
            {CALENDAR_APPS.map(app => (
              <details key={app.name} className="group bg-radar-surface border border-radar-border rounded-xl">
                <summary className="flex items-center gap-3 p-4 cursor-pointer list-none">
                  <span className="text-xl">{app.icon}</span>
                  <span className="font-medium text-sm">{app.name}</span>
                  <ChevronIcon />
                </summary>
                <ol className="px-6 pb-5 space-y-2">
                  {app.steps.map((step, i) => (
                    <li key={i} className="flex gap-3 text-sm text-radar-muted">
                      <span className="font-mono text-radar-green shrink-0">{i + 1}.</span>
                      {step}
                    </li>
                  ))}
                </ol>
              </details>
            ))}
          </div>
        </section>

        {/* Note */}
        <p className="text-xs text-radar-muted text-center leading-relaxed">
          The feed updates nightly at 11 PM. Your calendar app controls the refresh frequency —
          most sync every 24 hours.
        </p>
      </div>
    </div>
  )
}

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={`relative w-9 h-5 rounded-full transition-colors duration-200 ${
        checked ? 'bg-radar-green' : 'bg-radar-border'
      }`}
    >
      <span
        className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform duration-200 ${
          checked ? 'translate-x-4' : 'translate-x-0'
        }`}
      />
    </button>
  )
}

function ChevronIcon() {
  return (
    <svg
      width="14" height="14" viewBox="0 0 16 16" fill="none"
      className="ml-auto text-radar-muted group-open:rotate-180 transition-transform duration-200"
    >
      <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

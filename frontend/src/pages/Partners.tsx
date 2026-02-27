import { useState, FormEvent } from 'react'
import { registerPartner } from '../api'
import { EventCategory, PartnerRegistration } from '../types'

const CATEGORIES: EventCategory[] = [
  'arts', 'film', 'music', 'food', 'sports',
  'tech', 'community', 'outdoor', 'wellness', 'other',
]

const PERKS = [
  {
    icon: '📍',
    title: 'Exclusive badge',
    body: 'Your events appear with an "Exclusive" marker in every subscriber\'s calendar.',
  },
  {
    icon: '📅',
    title: 'Direct to calendars',
    body: 'Events push automatically to thousands of people looking for things to do.',
  },
  {
    icon: '⚡',
    title: 'Live in minutes',
    body: 'Register, get your API key, and submit your first event via our simple API.',
  },
  {
    icon: '🎯',
    title: 'Intent-first audience',
    body: 'Reach people who specifically subscribed to discover new experiences.',
  },
]

type Step = 'form' | 'success'

export function Partners() {
  const [step, setStep] = useState<Step>('form')
  const [result, setResult] = useState<{ api_key: string; business_name: string } | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [keyCopied, setKeyCopied] = useState(false)

  const [form, setForm] = useState<PartnerRegistration>({
    business_name: '',
    contact_email: '',
    website: '',
    description: '',
    category: undefined,
  })

  const set = (k: keyof PartnerRegistration) => (v: string) =>
    setForm(f => ({ ...f, [k]: v }))

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const res = await registerPartner(form)
      setResult(res)
      setStep('success')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const copyKey = () => {
    if (!result?.api_key) return
    navigator.clipboard.writeText(result.api_key).then(() => {
      setKeyCopied(true)
      setTimeout(() => setKeyCopied(false), 2000)
    })
  }

  return (
    <div className="min-h-screen pt-24 pb-16 px-6">
      <div className="max-w-5xl mx-auto space-y-20">
        {/* Header */}
        <div className="max-w-2xl space-y-4">
          <div className="inline-flex items-center gap-2 bg-radar-green/10 border border-radar-green/20 px-3 py-1 rounded-full">
            <span className="w-1.5 h-1.5 rounded-full bg-radar-green animate-pulse-slow" />
            <span className="text-radar-green text-xs font-semibold">Partner Program</span>
          </div>
          <h1 className="text-4xl font-bold tracking-tight">
            Put your events in front of Philadelphia's most curious people
          </h1>
          <p className="text-radar-muted leading-relaxed">
            Radar subscribers opt in to discover new experiences. Partner with us to submit
            exclusive events that show up directly in their calendars — pop-ups, tastings,
            screenings, private sessions, whatever moves your needle.
          </p>
        </div>

        {/* Perks */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {PERKS.map(p => (
            <div key={p.title} className="p-5 bg-radar-surface border border-radar-border rounded-xl space-y-3">
              <span className="text-2xl">{p.icon}</span>
              <h3 className="font-semibold text-sm">{p.title}</h3>
              <p className="text-radar-muted text-xs leading-relaxed">{p.body}</p>
            </div>
          ))}
        </div>

        {/* Form or success */}
        <div className="max-w-xl">
          {step === 'form' && (
            <form onSubmit={submit} className="space-y-5">
              <h2 className="text-xl font-semibold">Register your business</h2>

              <Field label="Business name" required>
                <input
                  type="text"
                  required
                  value={form.business_name}
                  onChange={e => set('business_name')(e.target.value)}
                  className="input w-full"
                  placeholder="The Meridian Bar"
                />
              </Field>

              <Field label="Contact email" required>
                <input
                  type="email"
                  required
                  value={form.contact_email}
                  onChange={e => set('contact_email')(e.target.value)}
                  className="input w-full"
                  placeholder="hello@yourplace.com"
                />
              </Field>

              <Field label="Website">
                <input
                  type="url"
                  value={form.website}
                  onChange={e => set('website')(e.target.value)}
                  className="input w-full"
                  placeholder="https://yourplace.com"
                />
              </Field>

              <Field label="Category">
                <select
                  value={form.category ?? ''}
                  onChange={e => setForm(f => ({ ...f, category: (e.target.value as EventCategory) || undefined }))}
                  className="input w-full bg-radar-surface"
                >
                  <option value="">Select a category</option>
                  {CATEGORIES.map(c => (
                    <option key={c} value={c}>
                      {c.charAt(0).toUpperCase() + c.slice(1)}
                    </option>
                  ))}
                </select>
              </Field>

              <Field label="Tell us about your business">
                <textarea
                  rows={3}
                  value={form.description}
                  onChange={e => set('description')(e.target.value)}
                  className="input w-full resize-none"
                  placeholder="What you do, the vibe, who you're for..."
                />
              </Field>

              {error && (
                <p className="text-red-400 text-sm bg-red-400/10 border border-red-400/20 px-4 py-3 rounded-lg">
                  {error}
                </p>
              )}

              <button type="submit" disabled={loading} className="btn-primary w-full py-3 text-base">
                {loading ? 'Registering...' : 'Register & Get API Key'}
              </button>

              <p className="text-xs text-radar-muted text-center">
                Free to join. No commitments.
              </p>
            </form>
          )}

          {step === 'success' && result && (
            <div className="space-y-8 animate-slide-up">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">🎉</span>
                  <h2 className="text-xl font-semibold">Welcome to Radar, {result.business_name}!</h2>
                </div>
                <p className="text-radar-muted text-sm">
                  Your API key is below. Store it securely — it won't be shown again.
                </p>
              </div>

              <div className="p-4 bg-radar-surface border border-radar-green/30 rounded-xl space-y-3">
                <p className="text-xs font-semibold uppercase tracking-widest text-radar-green">Your API Key</p>
                <code className="block font-mono text-sm text-radar-text break-all">
                  {result.api_key}
                </code>
                <button onClick={copyKey} className="btn-primary text-xs px-4 py-2">
                  {keyCopied ? 'Copied!' : 'Copy key'}
                </button>
              </div>

              <div className="p-5 bg-radar-surface border border-radar-border rounded-xl space-y-4">
                <p className="text-sm font-medium">Submit your first exclusive event:</p>
                <pre className="text-xs text-radar-muted overflow-x-auto leading-relaxed">
{`curl -X POST https://radar.philly/api/partners/events \\
  -H "X-Api-Key: YOUR_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "title": "Friday Night Tasting",
    "start_dt": "2025-04-04T19:00:00-05:00",
    "venue_name": "The Meridian Bar",
    "category": "food",
    "is_free": false,
    "price_min": 25
  }'`}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label className="block text-sm font-medium text-radar-text">
        {label}{required && <span className="text-radar-green ml-0.5">*</span>}
      </label>
      {children}
    </div>
  )
}

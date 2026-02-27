import { Event, EventFilters, PartnerRegistration } from './types'

const BASE = '/api'

function qs(params: Record<string, string | boolean | number | undefined>): string {
  const p = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== '' && v !== null) {
      p.set(k, String(v))
    }
  }
  const s = p.toString()
  return s ? `?${s}` : ''
}

export async function fetchEvents(filters: EventFilters = {}, limit = 60, offset = 0): Promise<Event[]> {
  const params: Record<string, string | boolean | number | undefined> = {
    limit,
    offset,
    ...(filters.category ? { category: filters.category } : {}),
    ...(filters.is_free !== '' && filters.is_free !== undefined ? { is_free: filters.is_free } : {}),
    ...(filters.is_exclusive !== '' && filters.is_exclusive !== undefined ? { is_exclusive: filters.is_exclusive } : {}),
    ...(filters.search ? { search: filters.search } : {}),
    ...(filters.start_after ? { start_after: filters.start_after } : {}),
  }
  const res = await fetch(`${BASE}/events${qs(params)}`)
  if (!res.ok) throw new Error('Failed to fetch events')
  return res.json()
}

export async function fetchEvent(id: string): Promise<Event> {
  const res = await fetch(`${BASE}/events/${id}`)
  if (!res.ok) throw new Error('Event not found')
  return res.json()
}

export function icalFeedUrl(filters: EventFilters = {}): string {
  const params: Record<string, string | boolean | undefined> = {
    ...(filters.category ? { category: filters.category } : {}),
    ...(filters.is_free !== '' && filters.is_free !== undefined ? { is_free: filters.is_free } : {}),
    ...(filters.is_exclusive !== '' && filters.is_exclusive !== undefined ? { is_exclusive: filters.is_exclusive } : {}),
  }
  return `${window.location.origin}${BASE}/events/feed.ics${qs(params)}`
}

export async function registerPartner(data: PartnerRegistration): Promise<{ api_key: string; message: string; id: string; business_name: string }> {
  const res = await fetch(`${BASE}/partners/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? 'Registration failed')
  }
  return res.json()
}

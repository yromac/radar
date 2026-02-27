import { useState } from 'react'
import { EventFilters } from '../types'
import { EventCard } from '../components/EventCard'
import { FilterBar } from '../components/FilterBar'
import { useEvents } from '../hooks/useEvents'

export function Events() {
  const [filters, setFilters] = useState<EventFilters>({})
  const { events, loading, error } = useEvents(filters)

  return (
    <div className="min-h-screen pt-24 pb-16 px-6">
      <div className="max-w-6xl mx-auto space-y-10">
        {/* Header */}
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight">Philadelphia Events</h1>
          <p className="text-radar-muted text-sm">
            {loading ? 'Scanning...' : `${events.length} events found`}
          </p>
        </div>

        {/* Filters */}
        <FilterBar filters={filters} onChange={setFilters} />

        {/* States */}
        {error && (
          <div className="text-center py-20 space-y-3">
            <p className="text-red-400 text-sm">{error}</p>
            <p className="text-radar-muted text-xs">Make sure the Radar API is running on localhost:8000</p>
          </div>
        )}

        {loading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {Array.from({ length: 9 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        )}

        {!loading && !error && events.length === 0 && (
          <div className="text-center py-32 space-y-3">
            <div className="flex justify-center opacity-20">
              <RadarEmpty />
            </div>
            <p className="text-radar-muted">No events match your filters.</p>
            <button
              onClick={() => setFilters({})}
              className="text-radar-green text-sm hover:underline"
            >
              Clear filters
            </button>
          </div>
        )}

        {!loading && !error && events.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {events.map(event => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function SkeletonCard() {
  return (
    <div className="card animate-pulse">
      <div className="aspect-[16/9] bg-radar-surface" />
      <div className="p-4 space-y-3">
        <div className="flex gap-2">
          <div className="h-5 w-16 bg-radar-surface rounded-md" />
          <div className="h-5 w-12 bg-radar-surface rounded-md" />
        </div>
        <div className="h-4 bg-radar-surface rounded w-4/5" />
        <div className="h-4 bg-radar-surface rounded w-3/5" />
        <div className="pt-2 border-t border-radar-border space-y-2">
          <div className="h-3 bg-radar-surface rounded w-2/5" />
          <div className="h-3 bg-radar-surface rounded w-3/5" />
        </div>
      </div>
    </div>
  )
}

function RadarEmpty() {
  return (
    <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
      <circle cx="40" cy="40" r="38" stroke="#00FF88" strokeWidth="1.5" />
      <circle cx="40" cy="40" r="25" stroke="#00FF88" strokeWidth="1.5" />
      <circle cx="40" cy="40" r="12" stroke="#00FF88" strokeWidth="1.5" />
      <circle cx="40" cy="40" r="3" fill="#00FF88" />
    </svg>
  )
}

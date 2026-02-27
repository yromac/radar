import { EventCategory, EventFilters } from '../types'
import { CategoryPill } from './CategoryBadge'

const CATEGORIES: Array<EventCategory | 'all'> = [
  'all', 'arts', 'film', 'music', 'food', 'tech',
  'community', 'outdoor', 'wellness', 'sports',
]

interface Props {
  filters: EventFilters
  onChange: (f: EventFilters) => void
}

export function FilterBar({ filters, onChange }: Props) {
  const setCategory = (cat: EventCategory | 'all') =>
    onChange({ ...filters, category: cat === 'all' ? '' : cat })

  const toggleFree = () =>
    onChange({ ...filters, is_free: filters.is_free === true ? '' : true })

  const toggleExclusive = () =>
    onChange({ ...filters, is_exclusive: filters.is_exclusive === true ? '' : true })

  const setSearch = (v: string) =>
    onChange({ ...filters, search: v || undefined })

  return (
    <div className="space-y-4">
      {/* Search */}
      <div className="relative">
        <SearchIcon />
        <input
          type="text"
          placeholder="Search events..."
          defaultValue={filters.search ?? ''}
          onChange={e => setSearch(e.target.value)}
          className="input w-full pl-9"
        />
      </div>

      {/* Category pills */}
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

      {/* Toggles */}
      <div className="flex items-center gap-3">
        <ToggleButton
          active={filters.is_free === true}
          onClick={toggleFree}
          label="Free only"
        />
        <ToggleButton
          active={filters.is_exclusive === true}
          onClick={toggleExclusive}
          label="★ Exclusive"
        />
      </div>
    </div>
  )
}

function ToggleButton({ active, onClick, label }: { active: boolean; onClick: () => void; label: string }) {
  return (
    <button
      onClick={onClick}
      className={`pill text-xs ${active ? 'pill-active' : ''}`}
    >
      {label}
    </button>
  )
}

function SearchIcon() {
  return (
    <svg
      width="16" height="16" viewBox="0 0 16 16" fill="none"
      className="absolute left-3 top-1/2 -translate-y-1/2 text-radar-muted pointer-events-none"
    >
      <circle cx="6.5" cy="6.5" r="5" stroke="currentColor" strokeWidth="1.4" />
      <path d="M10 10l3.5 3.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  )
}

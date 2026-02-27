import { EventCategory } from '../types'

const config: Record<EventCategory, { label: string; color: string }> = {
  arts:      { label: 'Arts',      color: 'text-purple-400 bg-purple-400/10 border-purple-400/20' },
  film:      { label: 'Film',      color: 'text-red-400 bg-red-400/10 border-red-400/20' },
  music:     { label: 'Music',     color: 'text-pink-400 bg-pink-400/10 border-pink-400/20' },
  food:      { label: 'Food',      color: 'text-orange-400 bg-orange-400/10 border-orange-400/20' },
  sports:    { label: 'Sports',    color: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20' },
  tech:      { label: 'Tech',      color: 'text-blue-400 bg-blue-400/10 border-blue-400/20' },
  community: { label: 'Community', color: 'text-teal-400 bg-teal-400/10 border-teal-400/20' },
  outdoor:   { label: 'Outdoor',   color: 'text-green-400 bg-green-400/10 border-green-400/20' },
  wellness:  { label: 'Wellness',  color: 'text-cyan-400 bg-cyan-400/10 border-cyan-400/20' },
  other:     { label: 'Other',     color: 'text-radar-muted bg-radar-muted/10 border-radar-muted/20' },
}

export function CategoryBadge({ category }: { category: EventCategory }) {
  const { label, color } = config[category] ?? config.other
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${color}`}>
      {label}
    </span>
  )
}

export function CategoryPill({
  category,
  active,
  onClick,
}: {
  category: EventCategory | 'all'
  active: boolean
  onClick: () => void
}) {
  const label = category === 'all' ? 'All' : config[category as EventCategory]?.label ?? category
  return (
    <button
      onClick={onClick}
      className={`pill ${active ? 'pill-active' : ''}`}
    >
      {label}
    </button>
  )
}

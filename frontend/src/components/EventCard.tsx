import { format, isToday, isTomorrow } from 'date-fns'
import { Event } from '../types'
import { CategoryBadge } from './CategoryBadge'

function formatDate(dt: string): string {
  const d = new Date(dt)
  if (isToday(d)) return `Today · ${format(d, 'h:mm a')}`
  if (isTomorrow(d)) return `Tomorrow · ${format(d, 'h:mm a')}`
  return format(d, 'EEE, MMM d · h:mm a')
}

function formatPrice(event: Event): string {
  if (event.is_free) return 'Free'
  if (event.price_min != null) {
    if (event.price_max && event.price_max !== event.price_min) {
      return `$${event.price_min}–$${event.price_max}`
    }
    return `$${event.price_min}`
  }
  return ''
}

const SOURCE_LABEL: Record<string, string> = {
  luma:                 'Luma',
  philly_film_festival: 'Film Society',
  museum:               'Museum',
  best_of_city:         'City Pick',
  partner:              'Partner',
}

export function EventCard({ event }: { event: Event }) {
  const price = formatPrice(event)

  return (
    <article className="card group flex flex-col animate-fade-in">
      {/* Image */}
      <div className="relative aspect-[16/9] bg-radar-surface overflow-hidden">
        {event.image_url ? (
          <img
            src={event.image_url}
            alt={event.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <RadarBlip />
          </div>
        )}

        {/* Exclusive badge */}
        {event.is_exclusive && (
          <span className="absolute top-3 left-3 bg-radar-green text-radar-bg text-xs font-bold px-2 py-0.5 rounded-md tracking-wide">
            EXCLUSIVE
          </span>
        )}

        {/* Price badge */}
        {price && (
          <span className={`absolute top-3 right-3 text-xs font-semibold px-2 py-0.5 rounded-md ${
            event.is_free
              ? 'bg-green-500/20 text-green-400 border border-green-500/30'
              : 'bg-radar-bg/80 text-radar-text border border-radar-border'
          }`}>
            {price}
          </span>
        )}
      </div>

      {/* Content */}
      <div className="flex flex-col flex-1 p-4 gap-3">
        {/* Meta row */}
        <div className="flex items-center gap-2 flex-wrap">
          <CategoryBadge category={event.category} />
          <span className="text-xs text-radar-muted">
            {SOURCE_LABEL[event.source] ?? event.source}
          </span>
        </div>

        {/* Title */}
        <h3 className="font-semibold text-base leading-snug text-radar-text line-clamp-2 group-hover:text-radar-green transition-colors">
          {event.url ? (
            <a href={event.url} target="_blank" rel="noopener noreferrer" className="hover:underline">
              {event.title}
            </a>
          ) : event.title}
        </h3>

        {/* Description */}
        {event.description && (
          <p className="text-sm text-radar-muted line-clamp-2 leading-relaxed">
            {event.description}
          </p>
        )}

        {/* Footer */}
        <div className="mt-auto pt-2 border-t border-radar-border space-y-1.5">
          <div className="flex items-center gap-2 text-xs text-radar-muted">
            <ClockIcon />
            <span>{formatDate(event.start_dt)}</span>
          </div>
          {event.venue_name && (
            <div className="flex items-center gap-2 text-xs text-radar-muted">
              <PinIcon />
              <span className="truncate">{event.venue_name}</span>
            </div>
          )}
        </div>
      </div>
    </article>
  )
}

function RadarBlip() {
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
      <circle cx="20" cy="20" r="18" stroke="#00FF88" strokeWidth="1" opacity="0.15" />
      <circle cx="20" cy="20" r="11" stroke="#00FF88" strokeWidth="1" opacity="0.2" />
      <circle cx="20" cy="20" r="4" stroke="#00FF88" strokeWidth="1" opacity="0.3" />
      <circle cx="20" cy="20" r="2" fill="#00FF88" opacity="0.4" />
    </svg>
  )
}

function ClockIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 16 16" fill="none" className="shrink-0">
      <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
      <path d="M8 4.5V8l2.5 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  )
}

function PinIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 16 16" fill="none" className="shrink-0">
      <path d="M8 1.5C5.515 1.5 3.5 3.515 3.5 6c0 3.5 4.5 8.5 4.5 8.5s4.5-5 4.5-8.5c0-2.485-2.015-4.5-4.5-4.5Z" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="8" cy="6" r="1.5" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  )
}

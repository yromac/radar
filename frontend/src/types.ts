export type EventCategory =
  | 'arts' | 'film' | 'music' | 'food' | 'sports'
  | 'tech' | 'community' | 'outdoor' | 'wellness' | 'other'

export type EventSource =
  | 'luma' | 'philly_film_festival' | 'museum'
  | 'best_of_city' | 'partner'

export interface Event {
  id: string
  title: string
  description: string | null
  url: string | null
  image_url: string | null
  start_dt: string
  end_dt: string | null
  all_day: boolean
  venue_name: string | null
  venue_address: string | null
  lat: number | null
  lng: number | null
  source: EventSource
  category: EventCategory
  tags: string | null
  is_free: boolean | null
  price_min: number | null
  price_max: number | null
  is_exclusive: boolean
}

export interface Partner {
  id: string
  business_name: string
  contact_email: string
  website: string | null
  description: string | null
  category: EventCategory | null
  is_active: boolean
}

export interface PartnerRegistration {
  business_name: string
  contact_email: string
  website?: string
  description?: string
  category?: EventCategory
}

export interface EventFilters {
  category?: EventCategory | ''
  is_free?: boolean | ''
  is_exclusive?: boolean | ''
  search?: string
  start_after?: string
}

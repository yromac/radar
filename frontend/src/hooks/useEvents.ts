import { useState, useEffect, useCallback } from 'react'
import { fetchEvents } from '../api'
import { Event, EventFilters } from '../types'

export function useEvents(filters: EventFilters) {
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchEvents(filters)
      setEvents(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }, [JSON.stringify(filters)])

  useEffect(() => { load() }, [load])

  return { events, loading, error, reload: load }
}

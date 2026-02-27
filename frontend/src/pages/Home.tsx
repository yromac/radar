import { Link } from 'react-router-dom'
import { RadarLogo } from '../components/RadarLogo'

const SOURCES = [
  { name: 'Luma',           desc: 'Meetups & tech events' },
  { name: 'Film Society',   desc: 'Screenings & festivals' },
  { name: 'PMA',            desc: 'Museum programming' },
  { name: 'Barnes',         desc: 'Art & lectures' },
  { name: 'Franklin',       desc: 'Science events' },
  { name: 'Eventbrite',     desc: 'City-wide listings' },
  { name: 'Visit Philly',   desc: 'Curated city picks' },
  { name: 'Partners',       desc: 'Exclusive local events' },
]

const HOW_IT_WORKS = [
  {
    step: '01',
    title: 'Radar scans',
    body: 'Every night at 11 PM, Radar sweeps Luma, Eventbrite, museum sites, the Film Society, and partner feeds.',
  },
  {
    step: '02',
    title: 'We curate',
    body: 'Duplicates get removed. Events get tagged by category, price, and exclusivity. Only the good stuff stays.',
  },
  {
    step: '03',
    title: 'Your calendar fills itself',
    body: 'Subscribe once with your calendar app and new events appear automatically. No app to open. No algorithm to fight.',
  },
]

export function Home() {
  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="relative flex flex-col items-center justify-center text-center px-6 pt-40 pb-32 overflow-hidden">
        {/* Background rings */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none select-none">
          {[600, 480, 360, 240].map(d => (
            <div
              key={d}
              className="absolute rounded-full border border-radar-green/10"
              style={{ width: d, height: d }}
            />
          ))}
          {/* Sweep gradient */}
          <div
            className="absolute rounded-full opacity-10"
            style={{
              width: 600, height: 600,
              background: 'conic-gradient(from 0deg, transparent 70%, #00aa55 100%)',
              animation: 'sweep 8s linear infinite',
            }}
          />
        </div>

        <div className="relative z-10 max-w-3xl mx-auto space-y-8 animate-slide-up">
          <div className="flex justify-center">
            <RadarLogo size={56} />
          </div>

          <h1 className="text-5xl sm:text-7xl font-black tracking-tighter leading-none">
            Stop doing the{' '}
            <span className="text-radar-green">same thing</span>{' '}
            every day.
          </h1>

          <p className="text-lg sm:text-xl text-radar-muted max-w-xl mx-auto leading-relaxed">
            Radar scans Philadelphia's best event platforms every night and pushes
            what's worth doing directly to your calendar.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/subscribe" className="btn-primary text-base px-8 py-3">
              Add to Calendar — Free
            </Link>
            <Link to="/events" className="btn-ghost text-base px-8 py-3">
              Browse Events
            </Link>
          </div>

          <p className="text-xs text-radar-muted font-mono">
            Works with Apple Calendar · Google Calendar · Outlook · Thunderbird
          </p>
        </div>
      </section>

      {/* Sources */}
      <section className="border-t border-radar-border py-20 px-6">
        <div className="max-w-5xl mx-auto">
          <p className="text-center text-xs text-radar-muted font-mono uppercase tracking-widest mb-10">
            Scanning
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-px bg-radar-border">
            {SOURCES.map(s => (
              <div key={s.name} className="bg-radar-bg p-6 space-y-1">
                <p className="font-semibold text-sm text-radar-text">{s.name}</p>
                <p className="text-xs text-radar-muted">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-24 px-6 border-t border-radar-border">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-center mb-16">
            How Radar works
          </h2>
          <div className="grid sm:grid-cols-3 gap-8">
            {HOW_IT_WORKS.map(item => (
              <div key={item.step} className="space-y-4">
                <span className="font-mono text-xs text-radar-green">{item.step}</span>
                <h3 className="text-xl font-semibold">{item.title}</h3>
                <p className="text-radar-muted text-sm leading-relaxed">{item.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Partner CTA */}
      <section className="py-20 px-6 border-t border-radar-border">
        <div className="max-w-2xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center gap-2 bg-radar-green/10 border border-radar-green/20 px-4 py-1.5 rounded-full">
            <span className="text-radar-green text-xs font-semibold">For Local Businesses</span>
          </div>
          <h2 className="text-3xl font-bold tracking-tight">
            Reach people actively looking for something to do
          </h2>
          <p className="text-radar-muted leading-relaxed">
            Partner with Radar to submit exclusive events — pop-ups, private tastings,
            after-hours — that show up with a badge in every subscriber's calendar.
          </p>
          <Link to="/partners" className="btn-primary inline-flex text-base px-8 py-3">
            Become a Partner
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-radar-border py-10 px-6">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-radar-muted">
          <div className="flex items-center gap-2">
            <RadarLogo size={18} />
            <span>Radar — Philadelphia</span>
          </div>
          <div className="flex gap-6">
            <Link to="/events" className="hover:text-radar-green transition-colors">Events</Link>
            <Link to="/subscribe" className="hover:text-radar-green transition-colors">Subscribe</Link>
            <Link to="/partners" className="hover:text-radar-green transition-colors">Partners</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}

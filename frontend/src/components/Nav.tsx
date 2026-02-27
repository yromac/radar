import { Link, NavLink } from 'react-router-dom'
import { RadarLogo } from './RadarLogo'

const links = [
  { to: '/events',    label: 'Events'    },
  { to: '/subscribe', label: 'Subscribe' },
  { to: '/partners',  label: 'Partners'  },
]

export function Nav() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-radar-border/60 bg-radar-bg/80 backdrop-blur-md">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <RadarLogo size={26} />
          <span className="font-bold text-lg tracking-tight text-radar-text group-hover:text-radar-green transition-colors">
            Radar
          </span>
          <span className="hidden sm:block text-xs text-radar-muted font-mono border border-radar-border px-1.5 py-0.5 rounded">
            PHL
          </span>
        </Link>

        {/* Nav links */}
        <nav className="flex items-center gap-1">
          {links.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-150 ${
                  isActive
                    ? 'text-radar-green bg-radar-green/10'
                    : 'text-radar-muted hover:text-radar-text'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
          <Link
            to="/subscribe"
            className="ml-3 btn-primary hidden sm:inline-flex"
          >
            Add to Calendar
          </Link>
        </nav>
      </div>
    </header>
  )
}

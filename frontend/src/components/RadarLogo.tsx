export function RadarLogo({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="16" cy="16" r="14" stroke="#00FF88" strokeWidth="1.2" opacity="0.2" />
      <circle cx="16" cy="16" r="9"  stroke="#00FF88" strokeWidth="1.2" opacity="0.35" />
      <circle cx="16" cy="16" r="4.5" stroke="#00FF88" strokeWidth="1.2" opacity="0.6" />
      <circle cx="16" cy="16" r="2"  fill="#00FF88" />
      {/* sweep arm */}
      <line x1="16" y1="16" x2="16" y2="3" stroke="#00FF88" strokeWidth="1.5" strokeLinecap="round" />
      {/* blip */}
      <circle cx="22" cy="9" r="1.5" fill="#00FF88" opacity="0.7" />
    </svg>
  )
}

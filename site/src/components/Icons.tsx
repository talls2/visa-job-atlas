// Inline SVGs, drawn with currentColor so they follow the theme.

export function Plane({ size = 20, className = "" }: { size?: number; className?: string }) {
  return (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M21.5 13.2v-1.6L13.4 7V2.9c0-.8-.6-1.4-1.4-1.4s-1.4.6-1.4 1.4V7L2.5 11.6v1.6l8.1-2.5v4.6l-2.2 1.6v1.3l3.6-1 3.6 1v-1.3l-2.2-1.6v-4.6z"
        transform="rotate(90 12 12)"
      />
    </svg>
  );
}

/** The opening flight: a dashed great-circle arc with a plane crossing it. */
export function FlightArc({ from, to }: { from: string; to: string }) {
  return (
    <svg className="arc" viewBox="0 0 600 120" role="img" aria-label={`${from} → ${to}`}>
      <path id="arc-path" d="M40 100 Q300 -20 560 100" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="2 9" strokeLinecap="round" />
      <circle cx="40" cy="100" r="5" fill="currentColor" />
      <circle cx="560" cy="100" r="5" fill="none" stroke="currentColor" strokeWidth="2" />
      <text x="40" y="118" textAnchor="middle" className="arc-code">{from}</text>
      <text x="560" y="118" textAnchor="middle" className="arc-code">{to}</text>
      <g className="arc-plane">
        <path
          fill="var(--signal)"
          d="M21.5 13.2v-1.6L13.4 7V2.9c0-.8-.6-1.4-1.4-1.4s-1.4.6-1.4 1.4V7L2.5 11.6v1.6l8.1-2.5v4.6l-2.2 1.6v1.3l3.6-1 3.6 1v-1.3l-2.2-1.6v-4.6z"
          transform="translate(-14 -14) scale(1.15) rotate(90 12 12)"
        />
      </g>
    </svg>
  );
}

export function Barcode({ seed = "VJA" }: { seed?: string }) {
  // Deterministic bars from the seed, so every ticket gets its own code.
  const bars: number[] = [];
  let h = 7;
  for (let i = 0; i < 46; i++) {
    h = (h * 31 + seed.charCodeAt(i % seed.length)) % 997;
    bars.push(1 + (h % 3));
  }
  let x = 0;
  return (
    <svg className="barcode" viewBox="0 0 140 36" preserveAspectRatio="none" aria-hidden="true">
      {bars.map((w, i) => {
        const r = i % 2 === 0 ? <rect key={i} x={x} y="0" width={w} height="36" fill="currentColor" /> : null;
        x += w + 0.6;
        return r;
      })}
    </svg>
  );
}

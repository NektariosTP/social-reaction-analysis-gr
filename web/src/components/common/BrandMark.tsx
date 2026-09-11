interface BrandMarkProps {
  size?: number;
  className?: string;
}

/**
 * Brand mark: a location pin with broadcast/signal arcs — collective action,
 * located + amplified. Uses `currentColor` so callers control the color and it
 * adapts to light/dark. The pin core uses the accent-contrast token.
 */
export function BrandMark({ size = 28, className }: BrandMarkProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      role="img"
      aria-label="protest.map"
      data-testid="brand-mark"
      className={className}
    >
      {/* signal waves radiating from the pin head */}
      <path
        d="M20.5 6.5a6 6 0 0 1 0 8.5"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        opacity="0.55"
      />
      <path
        d="M23.5 3.5a10.5 10.5 0 0 1 0 14.5"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        opacity="0.3"
      />
      {/* location pin */}
      <path
        d="M13 3a8 8 0 0 0-8 8c0 5.8 8 16 8 16s8-10.2 8-16a8 8 0 0 0-8-8Z"
        fill="currentColor"
      />
      {/* pin core */}
      <circle cx="13" cy="11" r="3" fill="var(--color-accent-contrast, #ffffff)" />
    </svg>
  );
}

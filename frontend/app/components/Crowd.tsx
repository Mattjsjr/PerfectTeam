import { motion } from "framer-motion";

// Deterministic pseudo-randomness so people/confetti don't reshuffle on every render,
// but still look organic rather than gridded.
const jitter = (i: number, amp: number) => Math.sin(i * 1.7) * amp;
const pseudo = (i: number) => {
  const raw = Math.sin(i * 12.9898) * 43758.5453;
  return raw - Math.floor(raw);
}

type Row = { count: number; y: number; spacing: number; headR: number; bodyW: number; bodyH: number; blur: string; opacity: number; colorClass: string; jumpEvery?: number };

// Used to control how many people are in the crowd
const rows: Row[] = [
  { count: 100, y: 14, spacing: 4, headR: 2, bodyW: 8, bodyH: 5, blur: "url(#blur-strong)", opacity: 0.2, colorClass: "text-muted-foreground" },
  { count: 100, y: 30, spacing: 4.2, headR: 3, bodyW: 12, bodyH: 8, blur: "url(#blur-strong)", opacity: 0.32, colorClass: "text-muted-foreground" },
  { count: 68, y: 50, spacing: 6.2, headR: 4.5, bodyW: 17, bodyH: 12, blur: "url(#blur-medium)", opacity: 0.62, colorClass: "text-primary", jumpEvery: 6 },
  { count: 44, y: 80, spacing: 10, headR: 6, bodyW: 22, bodyH: 16, blur: "url(#blur-light)", opacity: 0.92, colorClass: "text-chart-2", jumpEvery: 4 },
  { count: 44, y: 95, spacing: 10, headR: 6, bodyW: 22, bodyH: 16, blur: "url(#blur-light)", opacity: 0.92, colorClass: "text-chart-2", jumpEvery: 4 },
  { count: 44, y: 120, spacing: 10, headR: 6, bodyW: 22, bodyH: 16, blur: "url(#blur-light)", opacity: 0.92, colorClass: "text-chart-2", jumpEvery: 4 },
];

// Basic account-icon figure: filled head circle over a half-ellipse shoulder shape. No arms.
function Person({ cx, baseY, headR, bodyW, bodyH }: { cx: number; baseY: number; headR: number; bodyW: number; bodyH: number }) {
  const shoulderY = baseY - bodyH;
  return (
    <g fill="currentColor">
      <path d={`M${cx - bodyW / 2},${baseY} A${bodyW / 2},${bodyH} 0 0 1 ${cx + bodyW / 2},${baseY} Z`} />
      <circle cx={cx} cy={shoulderY - headR} r={headR} />
    </g>
  );
}

const confettiColors = ["text-primary", "text-chart-2", "text-chart-3", "text-chart-4", "text-secondary-foreground"];

function Confetti({ count }: { count: number }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => {
        const x = pseudo(i) * 400;
        const duration = 2.2 + pseudo(i + 50) * 1.6;
        const delay = pseudo(i + 100) * 2.5;
        const size = 3 + pseudo(i + 150) * 3;
        const color = confettiColors[i % confettiColors.length];
        return (
          <motion.rect
            key={i}
            x={x}
            width={size}
            height={size * 1.8}
            rx={1}
            className={color}
            fill="currentColor"
            initial={{ y: -15, rotate: 0, opacity: 0 }}
            animate={{ y: 145, rotate: 380, opacity: [0, 1, 1, 0] }}
            transition={{ duration, repeat: Infinity, ease: "linear", delay }}
          />
        );
      })}
    </>
  );
}

function Crowd() {
  return (
    <motion.svg
      viewBox="0 0 400 130"
      className="w-full h-40"
      xmlns="http://www.w3.org/2000/svg"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      <defs>
        <filter id="blur-strong" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="2.4" />
        </filter>
        <filter id="blur-medium" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="1.4" />
        </filter>
        <filter id="blur-light" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="0.6" />
        </filter>
      </defs>

      {rows.map((row, rowIndex) => (
        <g key={rowIndex} filter={row.blur} opacity={row.opacity} className={row.colorClass}>
          {Array.from({ length: row.count }).map((_, i) => {
            const cx = i * row.spacing + jitter(i + rowIndex * 7, row.spacing * 0.6);
            const isJumper = row.jumpEvery ? i % row.jumpEvery === 0 : false;
            const baseY = row.y + jitter(i + rowIndex * 3, 3) - (isJumper ? 10 : 0);

            const person = <Person cx={cx} baseY={baseY} headR={row.headR} bodyW={row.bodyW} bodyH={row.bodyH} />;

            if (!isJumper) return <g key={i}>{person}</g>;

            return (
              <motion.g
                key={i}
                animate={{ y: [0, -9, 0] }}
                transition={{ duration: 0.8 + pseudo(i + rowIndex * 20) * 0.5, repeat: Infinity, ease: "easeInOut", delay: pseudo(i + rowIndex * 40) * 1.5 }}
              >
                {person}
              </motion.g>
            );
          })}
        </g>
      ))}

      <Confetti count={22} />
    </motion.svg>
  );
}

export default Crowd;
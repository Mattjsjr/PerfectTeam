import { motion } from "framer-motion";

function Podium() {
  const flutes = [56, 66, 76, 86, 92]; // was 96, past the shaft's right edge (48+44=92)

  return (
    <svg viewBox="0 0 140 200" className="w-40 h-auto text-primary" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Baseline: the ground line the whole pedestal stands on. Draws first. */}
      <motion.line
        x1={15} y1={192} x2={125} y2={192}
        stroke="currentColor" strokeWidth={3} strokeLinecap="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
      />
      {/* Base flare: the trapezoid foot the shaft widens into at the bottom */}
      <motion.path
        d="M40,176 L100,176 L110,192 L30,192 Z"
        stroke="currentColor" strokeWidth={2.5} strokeLinejoin="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 0.35, ease: "easeInOut", delay: 0.25 }}
      />
      {/* Shaft: the tall rectangular column body */}
      <motion.rect
        x={48} y={66} width={44} height={110}
        stroke="currentColor" strokeWidth={2.5}
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 0.5, ease: "easeInOut", delay: 0.5 }}
      />
      {/* Flutes: 5 thin vertical grooves down the shaft, drawn as a quick staggered burst right after the shaft */}
      {flutes.map((x, i) => (
        <motion.line
          key={x}
          x1={x} y1={70} x2={x} y2={172}
          stroke="currentColor" strokeWidth={1} opacity={0.5}
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.3, ease: "easeInOut", delay: 0.9 + i * 0.06 }}
        />
      ))}
      {/* Neck: the short collar rectangle between the shaft and the capital */}
      <motion.rect
        x={55} y={52} width={30} height={14}
        stroke="currentColor" strokeWidth={2.5}
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 0.3, ease: "easeInOut", delay: 1.25 }}
      />
      {/* Capital flare: the curve widening from the neck out to the underside of the top disc */}
      <motion.path
        d="M32,27 C32,45 50,52 70,52 C90,52 108,45 108,27"
        stroke="currentColor" strokeWidth={2.5}
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 0.4, ease: "easeInOut", delay: 1.5 }}
      />
      {/* Trim ring: thin accent ellipse just under the top disc, in a second theme color */}
      <motion.ellipse
        cx={70} cy={25} rx={38} ry={7}
        className="text-chart-2"
        stroke="currentColor" strokeWidth={2}
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 0.35, ease: "easeInOut", delay: 1.85 }}
      />
      {/* Top disc: the flat surface the download button visually rests on. Draws last. */}
      <motion.ellipse
        cx={70} cy={18} rx={40} ry={9}
        stroke="currentColor" strokeWidth={2.5}
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 0.35, ease: "easeInOut", delay: 2.1 }}
      />
    </svg>
  );
}

export default Podium;
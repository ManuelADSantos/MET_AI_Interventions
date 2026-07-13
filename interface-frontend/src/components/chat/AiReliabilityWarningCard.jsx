import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'

const ENABLE_COLLAPSIBLE_WARNING_CARD = true

const bulletContainerVariants = {
  visible: { transition: { staggerChildren: 0.15, delayChildren: 0.3 } }
}

const bulletVariants = {
  hidden: { opacity: 0, y: 5 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.2, ease: 'easeOut' } }
}

const SEGMENTS = [
  { label: 'Low', color: '#ef4444', width: 50 },
  { label: 'Medium', color: '#f59e0b', width: 25 },
  { label: 'High', color: '#22c55e', width: 25 }
]

const CAROUSEL_INTERVAL_MS = 8000

const colorWithAlpha = (color, alpha) => {
  const fallback = `rgba(239,68,68,${alpha})`
  if (!color || typeof color !== 'string') return fallback

  const hex = color.trim().replace('#', '')
  const normalizedHex = hex.length === 3
    ? hex.split('').map((c) => `${c}${c}`).join('')
    : hex

  if (!/^[0-9a-fA-F]{6}$/.test(normalizedHex)) return fallback

  const r = parseInt(normalizedHex.slice(0, 2), 16)
  const g = parseInt(normalizedHex.slice(2, 4), 16)
  const b = parseInt(normalizedHex.slice(4, 6), 16)
  return `rgba(${r},${g},${b},${alpha})`
}

const getSegmentColorForPercent = (percent) => {
  let cumulativeWidth = 0
  const segment = SEGMENTS.find((s) => {
    cumulativeWidth += s.width
    return percent <= cumulativeWidth
  })

  return segment?.color || SEGMENTS[SEGMENTS.length - 1].color
}

const AiReliabilityWarningCard = ({ warning }) => {
  const { reliability, heading, entries } = warning
  const [isExpanded, setIsExpanded] = useState(true)
  const [strategyIndex, setStrategyIndex] = useState(0)
  const [showBullets, setShowBullets] = useState(false)
  const showExpandedCard = !ENABLE_COLLAPSIBLE_WARNING_CARD || isExpanded
  const visibleEntry = entries?.[strategyIndex]
  const reliabilityColor = reliability?.color || '#ef4444'
  const markerPercent = Math.min(100, Math.max(0, reliability?.markerValue ?? 100))
  const markerColor = getSegmentColorForPercent(markerPercent)
  const isLowReliability = reliability?.label?.toLowerCase() === 'low'
  const leftBackground = `linear-gradient(0deg, ${colorWithAlpha(reliabilityColor, 0.16)} 0%, ${colorWithAlpha(reliabilityColor, 0.07)} 36%, #ffffff 78%)`
  const neutralShadow = '0 16px 32px -22px rgba(0,0,0,0.42)'
  const cardShadow = isLowReliability
    ? '0 0 0 3px rgba(239,68,68,0.50), 0 0 32px -14px rgba(239,68,68,0.85), 0 16px 32px -22px rgba(0,0,0,0.42)'
    : neutralShadow
  const cardPulseShadows = [
    neutralShadow,
    `0 0 0 1px ${colorWithAlpha(reliabilityColor, 0.04)}, 0 0 14px -12px ${colorWithAlpha(reliabilityColor, 0.35)}, 0 16px 32px -22px rgba(0,0,0,0.42)`,
    cardShadow,
    `0 0 0 1px ${colorWithAlpha(reliabilityColor, 0.04)}, 0 0 14px -12px ${colorWithAlpha(reliabilityColor, 0.35)}, 0 16px 32px -22px rgba(0,0,0,0.42)`,
    neutralShadow,
    `0 0 0 1px ${colorWithAlpha(reliabilityColor, 0.035)}, 0 0 12px -12px ${colorWithAlpha(reliabilityColor, 0.28)}, 0 16px 32px -22px rgba(0,0,0,0.42)`,
    neutralShadow,
  ]

  // Marker slides from 0 -> target once the card has started entering
  const [markerPosition, setMarkerPosition] = useState(0)
  useEffect(() => {
    const t = setTimeout(() => setMarkerPosition(markerPercent), 100)
    return () => clearTimeout(t)
  }, [markerPercent])

  useEffect(() => {
    if (isExpanded || !entries?.length) return undefined

    const interval = setInterval(() => {
      setStrategyIndex((index) => (index + 1) % entries.length)
    }, CAROUSEL_INTERVAL_MS)

    return () => clearInterval(interval)
  }, [isExpanded, entries?.length])

  useEffect(() => {
    setStrategyIndex(0)
  }, [entries])

  useEffect(() => {
    setShowBullets(false)
    const id = requestAnimationFrame(() => setShowBullets(true))
    return () => cancelAnimationFrame(id)
  }, [entries])

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      exit={{
        opacity: 0,
        height: 0,
        transition: { duration: 0.16, ease: 'easeIn' }
      }}
      animate={{
        opacity: 1,
        y: 0,
        boxShadow: isLowReliability ? cardPulseShadows : cardShadow
      }}
      transition={{
        opacity: { duration: 0.35, ease: 'easeOut' },
        y: { duration: 0.35, ease: 'easeOut' },
        boxShadow: { duration: 2, ease: 'easeInOut', repeat: isLowReliability ? 5 : 0 }
      }}
      className="relative mx-auto w-full max-w-[var(--thread-max-width)] overflow-hidden rounded-2xl border border-[#e7e7e7] bg-white"
    >
      <AnimatePresence initial={false} mode="wait">
        {showExpandedCard ? (
          <motion.div
            key="expanded-warning"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: 'easeOut' }}
            className="overflow-hidden"
          >
            {ENABLE_COLLAPSIBLE_WARNING_CARD && (
              <button
                type="button"
                onClick={() => setIsExpanded(false)}
                className="absolute right-3 top-3 z-20 rounded-full bg-white/80 px-2 py-1 text-[11px] font-semibold text-[#737373] shadow-sm ring-1 ring-black/5 transition hover:bg-white hover:text-[#3f3f46]"
              >
                Hide
              </button>
            )}
            <div className="grid grid-cols-[10fr_12fr] divide-x divide-[#e7e7e7]">
              {/* Left: reliability estimate */}
              <div
                className="grid min-w-0 grid-rows-[auto_1fr] px-5 py-4"
                style={{ background: leftBackground }}
              >
                <div className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-widest text-[#a3a3a3]">
                  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="currentColor" stroke="none" aria-hidden="true">
                    <circle cx="12" cy="12" r="10" />
                    <rect x="11" y="10" width="2" height="7" fill="white" />
                    <circle cx="12" cy="7.5" r="1.1" fill="white" />
                  </svg>
                  AI Reliability Estimate
                </div>

                <div className="flex flex-col justify-center gap-1.5">
                  <p className="mt-2 text-[1rem] font-bold leading-tight text-[#050505]">
                    Reliability:{' '}
                    <span style={{ color: reliabilityColor }}>
                      {reliability?.label}
                    </span>
                  </p>

                  <div className="relative mt-3 pr-1">
                    <div
                      className="absolute -top-3 z-10"
                      style={{
                        left: `${markerPosition}%`,
                        width: 0,
                        height: 0,
                        marginLeft: -7,
                        borderLeft: '7px solid transparent',
                        borderRight: '7px solid transparent',
                        borderTop: `9px solid ${markerColor}`,
                        filter: 'drop-shadow(0 1px 1px rgba(0,0,0,0.16))',
                        transition: 'left 0.8s ease-out'
                      }}
                      aria-hidden="true"
                    />
                    <div className="flex h-5 w-full overflow-hidden rounded-full">
                      {SEGMENTS.map((segment) => (
                        <div
                          key={segment.label}
                          className="flex items-center justify-center text-[10px] font-bold uppercase tracking-wide text-white"
                          style={{ background: segment.color, width: `${segment.width}%` }}
                        >
                          {segment.label}
                        </div>
                      ))}
                    </div>
                    <div className="relative mt-1 h-3 text-[10px] font-medium text-[#b6b6b6]">
                      <span className="absolute left-0">0%</span>
                      <span className="absolute left-1/2 -translate-x-1/2">50%</span>
                      <span className="absolute left-3/4 -translate-x-1/2">75%</span>
                      <span className="absolute right-0">100%</span>
                    </div>
                  </div>

                  <div className="mt-2">
                    <p className="mb-0.5 text-[10px] font-semibold uppercase tracking-widest text-[#a3a3a3]">
                      
                    </p>
                    <p className="max-w-[95%] text-[1rem] font-medium leading-snug text-[#3f3f46]">
                      {reliability?.explanatoryText}
                    </p>
                  </div>
                </div>
              </div>

              {/* Right: strategies to watch for */}
          <div className="flex min-w-0 flex-col gap-3 bg-[#fdfdfd] px-5 py-4">
            <p className="text-[1rem] font-bold leading-tight text-[#050505]">{heading}</p>
            <motion.ul
              variants={bulletContainerVariants}
                  initial="hidden"
                  animate={showBullets ? 'visible' : 'hidden'}
                  className="flex flex-col gap-3"
                >
                  {(entries || []).map((entry, i) => (
                    <motion.li key={i} variants={bulletVariants} className="flex items-start gap-3">
                      <span className="mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full bg-[#d9d9d9]" aria-hidden="true" />
                      <div className="text-[.9rem] leading-full">
                        <p className="font text-[#050505]">{entry.title}</p>
                        <p className="mt-0.5 text-[#6a6a6a]">{entry.description}</p>
                      </div>
                </motion.li>
              ))}
            </motion.ul>
          </div>
            </div>
          </motion.div>
        ) : (
          <motion.button
            key="collapsed-warning"
            type="button"
            onClick={() => setIsExpanded(true)}
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.18, ease: 'easeOut' }}
            className="grid w-full grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)_auto] items-center gap-4 px-5 py-3 text-left"
            style={{ background: leftBackground }}
          >
            <div className="min-w-0">
              <div className="flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-widest text-[#a3a3a3]">
                AI Reliability Estimate
              </div>
              <p className="mt-1 truncate text-[17px] font-semibold text-[#050505]">
                Reliability:{' '}
                <span className="text-[18px] font-bold" style={{ color: reliabilityColor }}>{reliability?.label}</span>
              </p>
            </div>
            <div className="min-w-0 rounded-lg bg-white/65 px-3 py-2 shadow-sm ring-1 ring-black/5">
              <div className="flex items-center justify-between gap-3">
                <p className="truncate text-[11px] font-bold text-[#050505]">{heading}</p>
                {!!entries?.length && (
                  <span className="shrink-0 text-[10px] font-semibold text-[#999]">
                    {strategyIndex + 1}/{entries.length}
                  </span>
                )}
              </div>
              <AnimatePresence mode="wait">
                <motion.p
                  key={strategyIndex}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  transition={{ duration: 0.18, ease: 'easeOut' }}
                  className="mt-1 truncate text-[12px] font-semibold text-[#555]"
                >
                  {visibleEntry ? visibleEntry.title : 'Open warning details'}
                </motion.p>
              </AnimatePresence>
            </div>
            <span className="shrink-0 rounded-full bg-white/80 px-2.5 py-1 text-[11px] font-semibold text-[#737373] shadow-sm ring-1 ring-black/5">
              Show
            </span>
          </motion.button>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default AiReliabilityWarningCard

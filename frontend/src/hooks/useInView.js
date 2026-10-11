/**
 * useInView — lightweight IntersectionObserver hook for scroll-triggered animations.
 *
 * Usage:
 *   const ref = useInView();
 *   <div ref={ref} className="inview-hidden">…</div>
 *
 * When the element enters the viewport the hook adds `inview-visible` which
 * transitions opacity + transform via the CSS in index.css.
 *
 * Automatically no-ops when `prefers-reduced-motion: reduce` is set.
 */
import { useEffect, useRef } from "react";

const prefersReduced = typeof window !== "undefined"
  ? window.matchMedia("(prefers-reduced-motion: reduce)").matches
  : false;

export default function useInView(options = {}) {
  const ref = useRef(null);

  useEffect(() => {
    if (prefersReduced || !ref.current) return;

    const el = ref.current;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.classList.add("inview-visible");
          observer.unobserve(el); // fire once
        }
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px", ...options }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return ref;
}

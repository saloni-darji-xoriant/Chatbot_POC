"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { downloadBlob } from "@/lib/download";

const MIN_ZOOM = 1;
const MAX_ZOOM = 4;
const ZOOM_STEP = 0.5;

const clampZoom = (z: number) => Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, z));

/** "…/power-cycle-procedure.png?x=1" -> "power-cycle-procedure.png" */
export function filenameFromUrl(url: string, fallback = "image.png"): string {
  try {
    const last = new URL(url, "http://localhost").pathname.split("/").filter(Boolean).pop();
    return last ? decodeURIComponent(last) : fallback;
  } catch {
    return fallback;
  }
}

async function downloadImage(src: string): Promise<void> {
  try {
    // fetch + blob so the browser saves the file instead of navigating —
    // the `download` attribute is ignored for cross-origin URLs.
    // cache: "reload" because the <img> may already have cached this URL without CORS
    // headers, and reusing that copy makes a cross-origin fetch fail.
    const res = await fetch(src, { cache: "reload" });
    if (!res.ok) throw new Error(String(res.status));
    downloadBlob(await res.blob(), filenameFromUrl(src));
  } catch {
    window.open(src, "_blank", "noopener,noreferrer");
  }
}

interface ImageViewerProps {
  src: string;
  alt: string;
  caption?: string | null;
}

/**
 * An image in a chat answer that can be opened full-screen, zoomed
 * (buttons, +/- keys, Ctrl+wheel, double-click) and downloaded.
 */
export function ImageViewer({ src, alt, caption }: ImageViewerProps) {
  const [open, setOpen] = useState(false);
  const [zoom, setZoom] = useState(1);
  const openerRef = useRef<HTMLButtonElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const close = useCallback(() => {
    setOpen(false);
    setZoom(1);
    openerRef.current?.focus();
  }, []);

  useEffect(() => {
    if (!open) return;
    closeRef.current?.focus();
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
      else if (e.key === "+" || e.key === "=") setZoom((z) => clampZoom(z + ZOOM_STEP));
      else if (e.key === "-" || e.key === "_") setZoom((z) => clampZoom(z - ZOOM_STEP));
      else if (e.key === "0") setZoom(1);
    };
    // Native, non-passive listener so Ctrl/Cmd+wheel zooms the image instead of the page.
    const onWheel = (e: WheelEvent) => {
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        setZoom((z) => clampZoom(z + (e.deltaY < 0 ? ZOOM_STEP : -ZOOM_STEP)));
      }
    };
    const scroller = scrollRef.current;
    scroller?.addEventListener("wheel", onWheel, { passive: false });
    window.addEventListener("keydown", onKey);
    return () => {
      scroller?.removeEventListener("wheel", onWheel);
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = previousOverflow;
    };
  }, [open, close]);

  const toolbarButton =
    "flex h-9 min-w-9 items-center justify-center rounded-md bg-white/10 px-2.5 font-body text-sm font-medium text-white transition-colors hover:bg-white/20 disabled:cursor-not-allowed disabled:opacity-40";

  return (
    <figure className="m-0 max-w-[560px] overflow-hidden rounded-md border border-border bg-surface">
      <button
        ref={openerRef}
        type="button"
        onClick={() => setOpen(true)}
        aria-label={`Open image: ${alt}`}
        className="block w-full cursor-zoom-in"
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={src} alt={alt} loading="lazy" crossOrigin="anonymous" className="block h-auto w-full" />
      </button>

      <figcaption className="flex items-center justify-between gap-3 border-t border-border px-3 py-1.5 font-body text-xs text-text-dim">
        <span className="min-w-0 flex-1 truncate">{caption ?? alt}</span>
        <span className="flex shrink-0 items-center gap-3">
          <button type="button" onClick={() => setOpen(true)} className="font-medium text-accent hover:underline">
            Enlarge
          </button>
          <button
            type="button"
            onClick={() => downloadImage(src)}
            aria-label={`Download image: ${alt}`}
            className="font-medium text-accent hover:underline"
          >
            Download
          </button>
        </span>
      </figcaption>

      {open &&
        createPortal(
          <div
            role="dialog"
            aria-modal="true"
            aria-label={caption ?? alt}
            className="fixed inset-0 z-50 flex flex-col bg-black/85"
            onClick={(e) => {
              if (e.target === e.currentTarget) close();
            }}
          >
            <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-3">
              <p className="min-w-0 flex-1 truncate font-body text-sm text-white/90">{caption ?? alt}</p>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  aria-label="Zoom out"
                  className={toolbarButton}
                  disabled={zoom <= MIN_ZOOM}
                  onClick={() => setZoom((z) => clampZoom(z - ZOOM_STEP))}
                >
                  &minus;
                </button>
                <span aria-live="polite" className="w-12 text-center font-mono text-xs text-white/90">
                  {Math.round(zoom * 100)}%
                </span>
                <button
                  type="button"
                  aria-label="Zoom in"
                  className={toolbarButton}
                  disabled={zoom >= MAX_ZOOM}
                  onClick={() => setZoom((z) => clampZoom(z + ZOOM_STEP))}
                >
                  +
                </button>
                <button type="button" aria-label="Reset zoom" className={toolbarButton} onClick={() => setZoom(1)}>
                  Fit
                </button>
                <button
                  type="button"
                  aria-label="Download image"
                  className={toolbarButton}
                  onClick={() => downloadImage(src)}
                >
                  Download
                </button>
                <a
                  href={src}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label="Open image in a new tab"
                  className={toolbarButton}
                >
                  New tab
                </a>
                <button ref={closeRef} type="button" aria-label="Close image viewer" className={toolbarButton} onClick={close}>
                  Close
                </button>
              </div>
            </div>

            <div
              ref={scrollRef}
              className="flex min-h-0 flex-1 overflow-auto p-4"
              onClick={(e) => {
                if (e.target === e.currentTarget) close();
              }}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={src}
                alt={alt}
                draggable={false}
                onDoubleClick={() => setZoom((z) => (z > 1 ? 1 : 2))}
                className="m-auto rounded-md bg-white"
                style={
                  zoom === 1
                    ? { maxWidth: "100%", maxHeight: "100%", cursor: "zoom-in" }
                    : { width: `${zoom * 100}%`, maxWidth: "none", cursor: "zoom-out" }
                }
              />
            </div>
          </div>,
          document.body
        )}
    </figure>
  );
}

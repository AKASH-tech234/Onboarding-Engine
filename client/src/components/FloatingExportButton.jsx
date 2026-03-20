import React, { useState, useEffect } from 'react';
import { exportRoadmapPDF } from '../utils/exportRoadmapPDF';

export default function FloatingExportButton({ exportData }) {
  const [state, setState] = useState("idle");
  const [visible, setVisible] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 800);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const handleExport = async () => {
    if (state !== "idle" || !exportData) return;
    setState("loading");
    
    try {
      await exportRoadmapPDF(exportData);
      
      setState("done");
      setTimeout(() => setState("idle"), 2500);
      
    } catch (error) {
      console.error("PDF export failed:", error);
      setState("idle");
    }
  };

  const getStyle = () => {
    const base = {
      position: "fixed",
      bottom: isMobile ? "20px" : "32px",
      right: isMobile ? "16px" : "32px",
      zIndex: 9999,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      gap: "10px",
      padding: isMobile ? "14px" : "14px 24px",
      borderRadius: "999px",
      color: "white",
      fontSize: "14px",
      fontWeight: 500,
      cursor: "pointer",
      transition: "all 0.5s cubic-bezier(0.16,1,0.3,1)",
      backdropFilter: "blur(8px)",
      userSelect: "none",
      opacity: visible ? 1 : 0,
      transform: visible ? "translateY(0)" : "translateY(20px)",
      willChange: "transform"
    };

    if (state === "idle") {
      let idleStyle = {
        ...base,
        background: "linear-gradient(135deg, #4f8ef7 0%, #6366f1 100%)",
        border: "1px solid rgba(255,255,255,0.2)",
        boxShadow: `0 0 0 1px rgba(79,142,247,0.3), 0 8px 32px rgba(79,142,247,0.35), 0 2px 8px rgba(0,0,0,0.4)`
      };
      if (isHovered) {
        idleStyle.transform = visible ? "translateY(-2px) scale(1.02)" : idleStyle.transform;
        idleStyle.boxShadow = `0 0 0 1px rgba(79,142,247,0.5), 0 12px 40px rgba(79,142,247,0.45), 0 4px 12px rgba(0,0,0,0.4)`;
      }
      return idleStyle;
    }

    if (state === "loading") {
      return {
        ...base,
        background: "rgba(17,19,24,0.95)",
        border: "1px solid rgba(79,142,247,0.3)",
        boxShadow: `0 0 0 1px rgba(79,142,247,0.3), 0 8px 32px rgba(79,142,247,0.35), 0 2px 8px rgba(0,0,0,0.4)`,
        cursor: "wait"
      };
    }

    // done
    return {
      ...base,
      background: "rgba(16,185,129,0.15)",
      border: "1px solid rgba(16,185,129,0.4)",
      boxShadow: "0 0 0 1px rgba(16,185,129,0.2), 0 8px 32px rgba(16,185,129,0.2)"
    };
  };

  return (
    <>
      <style>{`
        @keyframes spinLoading {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes exportPulseRing {
          0%   { transform: scale(1);    opacity: 0.6; }
          100% { transform: scale(1.18); opacity: 0; }
        }
      `}</style>
      <div
        onClick={handleExport}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        style={getStyle()}
        role="button"
      >
        {state === "idle" && (
          <>
            <div style={{
              position: "absolute", inset: "-4px", borderRadius: "999px",
              border: "1px solid rgba(79,142,247,0.4)",
              animation: "exportPulseRing 2s ease-out infinite",
              pointerEvents: "none", zIndex: -1
            }} />
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 2v8M5 7l3 3 3-3M3 12h10" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            {!isMobile && <span>Export Roadmap</span>}
          </>
        )}

        {state === "loading" && (
          <>
            <svg width="16" height="16" viewBox="0 0 16 16" style={{animation: "spinLoading 0.8s linear infinite"}}>
              <circle cx="8" cy="8" r="6" stroke="rgba(255,255,255,0.2)" strokeWidth="2" fill="none"/>
              <path d="M8 2 A6 6 0 0 1 14 8" stroke="#4f8ef7" strokeWidth="2" strokeLinecap="round" fill="none"/>
            </svg>
            {!isMobile && <span>Generating PDF...</span>}
          </>
        )}

        {state === "done" && (
          <>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M3 8l3.5 3.5L13 5" stroke="#34d399" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            {!isMobile && <span style={{ color: "#34d399" }}>Downloaded!</span>}
          </>
        )}
      </div>
    </>
  );
}

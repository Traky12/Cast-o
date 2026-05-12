import React from "react";

// Sabionda.jsx - Componente de Referencia EU (v3.1)
const SABIONDA_OFICIAL = {
  src: "/assets/sabionda/sabionda-oficial.png",
  alt: "Sabionda IA - Experta Agrovoltaica + Admin TRL9",
  sizes: {
    header: "w-24 h-24",
    card: "w-32 h-32",
    full: "w-48 h-48",
  },
  fallback: "/assets/sabionda/fallback-holo.svg",
};

export function SabiondaAvatar({ variant = "header", context = "TRL9", className = "" }) {
  const sizeClass = SABIONDA_OFICIAL.sizes[variant] || SABIONDA_OFICIAL.sizes.header;
  return (
    <div className={`relative group sabionda-avatar ${className}`}>
      <img
        src={SABIONDA_OFICIAL.src}
        alt={SABIONDA_OFICIAL.alt}
        className={`${sizeClass} rounded-xl object-cover shadow-2xl ring-4 ring-[rgba(0,191,255,0.5)] hover:ring-[rgba(255,215,0,0.75)] transition-all duration-300`}
        onError={(e) => {
          e.target.src = SABIONDA_OFICIAL.fallback;
          e.target.classList.add("animate-pulse");
        }}
      />
      <div className="absolute -bottom-12 left-1/2 -translate-x-1/2 bg-amber-400/90 text-black px-3 py-1 rounded-full text-xs opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap pointer-events-none">
        Sabionda {context} | CTAEX €500K
      </div>
    </div>
  );
}

export const SabiondaProfile = ({
  variant = "profile",
  sizeClass = "h-32",
  className = "",
}) => {
  const label =
    variant === "tech"
      ? "Sabionda: tecnología y naturaleza"
      : "Sabionda: experta en agrovoltaica";
  const avatarVariant =
    sizeClass.includes("24") ? "header" : sizeClass.includes("48") ? "full" : "card";

  return (
    <div className={`flex flex-col items-center ${className}`}>
      <SabiondaAvatar variant={avatarVariant} context="TRL9_FEDERADA" />
      <p className="mt-2 text-sm font-medium text-gray-700 dark:text-gray-300 text-center">
        {label}
      </p>
    </div>
  );
};

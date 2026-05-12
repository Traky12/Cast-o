<?php
/**
 * Theme screenshot generator — outputs a simple SVG preview
 * for the WordPress theme browser. Rename to screenshot.png in production.
 */
header('Content-Type: image/svg+xml');
?>
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="900" viewBox="0 0 1200 900">
  <rect width="1200" height="900" fill="#0D2818"/>
  <rect y="50" width="1200" height="50" fill="#0A2214"/>
  <rect x="40" y="60" width="120" height="28" rx="4" fill="#BF9B30" opacity=".8"/>
  <rect x="800" y="62" width="80" height="24" rx="4" fill="#4A7C59" opacity=".6"/>
  <rect x="900" y="62" width="80" height="24" rx="4" fill="#4A7C59" opacity=".6"/>
  <rect x="1040" y="62" width="100" height="24" rx="8" fill="#BF9B30"/>
  <text x="600" y="280" font-family="sans-serif" font-size="56" font-weight="700" fill="#F7F3EE" text-anchor="middle">Agricultura inteligente.</text>
  <text x="600" y="350" font-family="sans-serif" font-size="56" font-weight="700" fill="#BF9B30" text-anchor="middle">Trazabilidad verificable.</text>
  <text x="600" y="420" font-family="sans-serif" font-size="22" fill="#F7F3EE" text-anchor="middle" opacity=".6">GaiaChain · IPFS · EU Sovereign · RGPD</text>
  <rect x="480" y="460" width="240" height="52" rx="8" fill="#BF9B30"/>
  <text x="600" y="493" font-family="sans-serif" font-size="18" font-weight="600" fill="#0D2818" text-anchor="middle">Solicitar catálogo B2B</text>
</svg>

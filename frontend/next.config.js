// next.config.js — CASTÚO Dashboard v1.7.5
// CSP headers ISO 27001 A.14.2.5 (seguridad en redes / transferencia de información)
// Usar cuando el frontend sea Next.js 14+ (por ahora extremadura-dashboard es CRA; CSP en nginx/Traefik o index.html)

module.exports = {
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Content-Security-Policy',
            value:
              "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; object-src 'none'; frame-ancestors 'none';",
          },
        ],
      },
    ];
  },
};

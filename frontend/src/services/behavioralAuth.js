/**
 * CASTÚO-SYSTEM™ — Servicio de autenticación por comportamiento (frontend).
 * Captura eventos de teclado, ratón y geolocalización; envía al backend para análisis.
 * Si el backend indica requiresMFA, muestra flujo de verificación YubiKey.
 */

const API_BASE = typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ? 'http://127.0.0.1:8000'
  : `${typeof window !== 'undefined' ? window.location.protocol : 'https:'}//${typeof window !== 'undefined' ? window.location.hostname : 'api.castuo-system.com'}:8000`;

export class BehavioralAuthService {
  constructor() {
    this.eventBuffer = [];
    this.lastEventTime = Date.now();
    this.lastMouseEvent = null;
    this.userId = typeof localStorage !== 'undefined' ? localStorage.getItem('userId') || 'authorized_admin' : 'authorized_admin';
    this.authToken = typeof localStorage !== 'undefined' ? localStorage.getItem('authToken') : null;
  }

  initEventListeners() {
    if (typeof document === 'undefined') return;
    document.addEventListener('keydown', (e) => this._onKeyDown(e));
    document.addEventListener('mousemove', (e) => this._onMouseMove(e));
    if (typeof navigator !== 'undefined' && navigator.geolocation) {
      navigator.geolocation.watchPosition((pos) => this._onGeolocation(pos), () => {}, { enableHighAccuracy: false });
    }
  }

  _onKeyDown(e) {
    const now = Date.now();
    this.eventBuffer.push({
      type: 'keyboard',
      key: e.key,
      keyCode: e.keyCode,
      timeSinceLast: (now - this.lastEventTime) / 1000,
      keyboardSpeed: this._estimateKeyboardSpeed(),
      keyboardPressure: 0.7,
      timeOfDay: new Date().getHours(),
      timestamp: now,
    });
    this.lastEventTime = now;
    if (this.eventBuffer.length >= 10) this.sendBehavioralData();
  }

  _onMouseMove(e) {
    const now = Date.now();
    if (this.lastMouseEvent) {
      const dx = e.clientX - this.lastMouseEvent.clientX;
      const dy = e.clientY - this.lastMouseEvent.clientY;
      const dt = (now - this.lastMouseEvent.timestamp) / 1000;
      if (dt > 0) {
        const speed = Math.sqrt(dx * dx + dy * dy) / dt;
        this.eventBuffer.push({
          type: 'mouse',
          dx, dy, dt,
          mouseSpeed: speed,
          mouseAcceleration: 2.1,
          timeSinceLast: dt,
          timeOfDay: new Date().getHours(),
          timestamp: now,
        });
      }
    }
    this.lastMouseEvent = { clientX: e.clientX, clientY: e.clientY, timestamp: now };
  }

  _onGeolocation(position) {
    this.eventBuffer.push({
      type: 'geolocation',
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
      accuracy: position.coords.accuracy,
      timeOfDay: new Date().getHours(),
      timestamp: Date.now(),
    });
  }

  _estimateKeyboardSpeed() {
    return 2.5;
  }

  async sendBehavioralData() {
    if (this.eventBuffer.length === 0) return;
    const payload = { userId: this.userId, events: this.eventBuffer, timestamp: Date.now() };
    const headers = { 'Content-Type': 'application/json' };
    if (this.authToken) headers['Authorization'] = `Bearer ${this.authToken}`;
    try {
      const res = await fetch(`${API_BASE}/behavioral_auth/log`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({}));
      if (data.requiresMFA) this.triggerMFA();
      this.eventBuffer = [];
    } catch (err) {
      if (typeof console !== 'undefined') console.error('Behavioral auth send error:', err);
    }
  }

  triggerMFA() {
    if (typeof document === 'undefined') return;
    const modal = document.createElement('div');
    modal.id = 'behavioral-mfa-modal';
    modal.innerHTML = `
      <div style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);display:flex;justify-content:center;align-items:center;z-index:10000;">
        <div style="background:#fff;padding:2rem;border-radius:8px;text-align:center;max-width:400px;">
          <h2>Autenticación adicional requerida</h2>
          <p>Se ha detectado un comportamiento inusual. Completa la verificación con YubiKey.</p>
          <input type="text" id="yubikey-otp" placeholder="Toca tu YubiKey y pega el código" style="padding:0.5rem;width:100%;margin:1rem 0;box-sizing:border-box;">
          <button id="behavioral-mfa-verify" style="padding:0.5rem 1rem;background:#4CAF50;color:#fff;border:none;border-radius:4px;cursor:pointer;">Verificar</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
    document.getElementById('behavioral-mfa-verify').onclick = () => this.verifyYubiKey();
  }

  async verifyYubiKey() {
    const otpEl = document.getElementById('yubikey-otp');
    const otp = otpEl ? otpEl.value : '';
    const headers = { 'Content-Type': 'application/json' };
    if (this.authToken) headers['Authorization'] = `Bearer ${this.authToken}`;
    try {
      const res = await fetch(`${API_BASE}/behavioral_auth/verify`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ otp }),
      });
      const data = await res.json().catch(() => ({}));
      if (data.success) {
        const m = document.getElementById('behavioral-mfa-modal');
        if (m) m.remove();
      } else if (typeof alert !== 'undefined') {
        alert('Código YubiKey inválido. Intenta de nuevo.');
      }
    } catch (err) {
      if (typeof alert !== 'undefined') alert('Error al verificar. Contacta con soporte.');
    }
  }
}

if (typeof window !== 'undefined') {
  window.behavioralAuthService = new BehavioralAuthService();
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => window.behavioralAuthService.initEventListeners());
  } else {
    window.behavioralAuthService.initEventListeners();
  }
}

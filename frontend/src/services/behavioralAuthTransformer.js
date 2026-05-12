/**
 * CASTÚO-SYSTEM™ — Autenticación por comportamiento (Transformer): captura avanzada.
 * Teclado, ratón, geolocalización, orientación; envía al backend /behavioral_auth/log.
 * BERT opcional (no cargado por defecto para evitar peso).
 */

const API_BASE = typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ? 'http://127.0.0.1:8000'
  : `${typeof window !== 'undefined' ? window.location.protocol : 'https:'}//${typeof window !== 'undefined' ? window.location.hostname : 'api.castuo-system.com'}:8000`;

export class BehavioralAuthTransformerService {
  constructor() {
    this.eventBuffer = [];
    this.lastEventTime = Date.now();
    this.lastMouseEvent = null;
    this.lastMouseSpeed = 0;
    this.userId = typeof localStorage !== 'undefined' ? localStorage.getItem('userId') || 'authorized_admin' : 'authorized_admin';
    this.authToken = typeof localStorage !== 'undefined' ? localStorage.getItem('authToken') : null;
    this.sendInterval = null;
  }

  initEventListeners() {
    if (typeof document === 'undefined') return;
    document.addEventListener('keydown', (e) => this._captureKey(e, false));
    document.addEventListener('keyup', (e) => this._captureKey(e, true));
    document.addEventListener('mousemove', (e) => this._captureMouse(e, false));
    document.addEventListener('mousedown', (e) => this._captureMouse(e, true));
    document.addEventListener('mouseup', (e) => this._captureMouse(e, false));
    if (typeof navigator !== 'undefined' && navigator.geolocation) {
      navigator.geolocation.watchPosition((p) => this._captureGeo(p), () => {}, { enableHighAccuracy: false });
    }
    if (typeof window !== 'undefined' && window.DeviceOrientationEvent) {
      window.addEventListener('deviceorientation', (e) => this._captureOrientation(e));
    }
    this.sendInterval = setInterval(() => { if (this.eventBuffer.length > 0) this.sendBehavioralData(); }, 5000);
  }

  _captureKey(e, isKeyUp) {
    const now = Date.now();
    this.eventBuffer.push({
      type: 'keyboard',
      key: e.key,
      keyCode: e.keyCode,
      code: e.code,
      shiftKey: e.shiftKey,
      ctrlKey: e.ctrlKey,
      altKey: e.altKey,
      metaKey: e.metaKey,
      timeSinceLast: (now - this.lastEventTime) / 1000,
      timeOfDay: new Date().getHours(),
      isKeyUp,
      keyboardSpeed: 2.5,
      keyboardPressure: 0.7,
      timestamp: now,
    });
    this.lastEventTime = now;
  }

  _captureMouse(e, isClick) {
    const now = Date.now();
    if (this.lastMouseEvent) {
      const dx = e.clientX - this.lastMouseEvent.clientX;
      const dy = e.clientY - this.lastMouseEvent.clientY;
      const dt = (now - this.lastMouseEvent.timestamp) / 1000;
      if (dt > 0 && (dx !== 0 || dy !== 0)) {
        const speed = Math.sqrt(dx * dx + dy * dy) / dt;
        const acc = this.lastMouseSpeed ? (speed - this.lastMouseSpeed) / dt : 0;
        this.lastMouseSpeed = speed;
        this.eventBuffer.push({
          type: 'mouse',
          clientX: e.clientX,
          clientY: e.clientY,
          movementX: e.movementX,
          movementY: e.movementY,
          buttons: e.buttons,
          isClick,
          mouseSpeed: speed,
          mouseAcceleration: acc,
          timeSinceLast: dt,
          timeOfDay: new Date().getHours(),
          timestamp: now,
        });
      }
    }
    this.lastMouseEvent = { clientX: e.clientX, clientY: e.clientY, timestamp: now };
  }

  _captureGeo(position) {
    this.eventBuffer.push({
      type: 'geolocation',
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
      geolocation_lat: position.coords.latitude,
      geolocation_lon: position.coords.longitude,
      accuracy: position.coords.accuracy,
      timeOfDay: new Date().getHours(),
      timestamp: Date.now(),
    });
  }

  _captureOrientation(e) {
    this.eventBuffer.push({
      type: 'device_orientation',
      device_orientation_x: e.alpha,
      device_orientation_y: e.beta,
      device_orientation_z: e.gamma,
      timeOfDay: new Date().getHours(),
      timestamp: Date.now(),
    });
  }

  async sendBehavioralData() {
    if (this.eventBuffer.length === 0) return;
    const headers = { 'Content-Type': 'application/json' };
    if (this.authToken) headers['Authorization'] = `Bearer ${this.authToken}`;
    try {
      const res = await fetch(`${API_BASE}/behavioral_auth/log`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ userId: this.userId, events: this.eventBuffer, timestamp: Date.now() }),
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
    modal.id = 'behavioral-mfa-modal-transformer';
    modal.innerHTML = `
      <div style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);display:flex;justify-content:center;align-items:center;z-index:10000;color:#fff;">
        <div style="background:#1a1a1a;padding:2rem;border-radius:8px;text-align:center;max-width:480px;">
          <h2 style="color:#ff5555;">Autenticación adicional requerida</h2>
          <p>Comportamiento inusual detectado. Verifica con YubiKey.</p>
          <input type="text" id="yubikey-otp-tx" placeholder="Código YubiKey" style="padding:0.5rem;width:100%;margin:1rem 0;box-sizing:border-box;background:#333;color:#fff;border:1px solid #555;">
          <button id="mfa-verify-tx" style="padding:0.5rem 1rem;background:#4CAF50;color:#fff;border:none;border-radius:4px;cursor:pointer;">Verificar</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
    document.getElementById('mfa-verify-tx').onclick = () => this.verifyYubiKey();
  }

  async verifyYubiKey() {
    const el = document.getElementById('yubikey-otp-tx');
    const otp = el ? el.value : '';
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
        const m = document.getElementById('behavioral-mfa-modal-transformer');
        if (m) m.remove();
      } else if (typeof alert !== 'undefined') alert('Código YubiKey inválido.');
    } catch (e) {
      if (typeof alert !== 'undefined') alert('Error al verificar.');
    }
  }
}

if (typeof window !== 'undefined') {
  window.behavioralAuthTransformerService = new BehavioralAuthTransformerService();
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => window.behavioralAuthTransformerService.initEventListeners());
  } else {
    window.behavioralAuthTransformerService.initEventListeners();
  }
}

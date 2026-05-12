/**
 * Esqueleto WebRTC: exige servidor de señalización propio y política de STUN/TURN acordada.
 * No enlaza a terceros en producción sin DPIA.
 */
(function () {
  const logEl = document.getElementById("log");
  function log(msg) {
    const t = new Date().toISOString();
    logEl.textContent = `${t} ${msg}\n` + logEl.textContent;
  }

  const pc = new RTCPeerConnection({
    iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
  });

  pc.ontrack = (event) => {
    if (event.track.kind === "video") {
      const v = document.getElementById("robotVideo");
      v.srcObject = event.streams[0];
      log("track video recibido");
    }
  };

  pc.oniceconnectionstatechange = () => log(`ice: ${pc.iceConnectionState}`);

  window.__castuoRtc = { pc, log };
})();

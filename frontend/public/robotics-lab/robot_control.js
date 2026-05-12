/**
 * Panel mínimo: los comandos reales deben pasar por auth del backend Castúo.
 */
(function () {
  const { pc, log } = window.__castuoRtc || {};

  function sendCommand(command) {
    if (!pc || !pc.dataChannel || pc.dataChannel.readyState !== "open") {
      log && log("dataChannel no listo (configurar signaling)");
      return;
    }
    pc.dataChannel.send(JSON.stringify(command));
  }

  document.getElementById("btnPing")?.addEventListener("click", () => {
    sendCommand({ type: "ping", ts: Date.now() });
  });

  window.castuoRobotControl = { sendCommand };
})();

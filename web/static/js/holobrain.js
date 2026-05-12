(() => {
  const root = document.documentElement;
  root.style.setProperty("--holobrain-pulse", "1");
  window.addEventListener(
    "mousemove",
    (e) => {
      const x = (e.clientX / window.innerWidth).toFixed(3);
      root.style.setProperty("--holobrain-x", x);
    },
    { passive: true },
  );
})();

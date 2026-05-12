<?php
/**
 * Template Name: Verificación de Trazabilidad QR
 * Allows buyers/logistics teams to verify a lot hash against blockchain.
 */
get_header();
?>

<main id="main" role="main">
  <section class="section verify-section" aria-labelledby="verify-heading">
    <div class="container">

      <div class="verify-card">
        <h2 id="verify-heading"><?php esc_html_e('Verificar trazabilidad de lote', 'castuo-agritech'); ?></h2>
        <p><?php esc_html_e('Introduce el ID de lote y el hash impreso en el QR para comprobar la integridad del registro en blockchain.', 'castuo-agritech'); ?></p>

        <form class="verify-form" id="verify-form" novalidate role="search" aria-label="<?php esc_attr_e('Verificador de lote', 'castuo-agritech'); ?>">
          <label class="sr-only" for="lote-input"><?php esc_html_e('ID de lote', 'castuo-agritech'); ?></label>
          <input
            type="text"
            id="lote-input"
            class="verify-input"
            placeholder="<?php esc_attr_e('ID lote (ej. INVH-ES28-MICGR-A4F2)', 'castuo-agritech'); ?>"
            pattern="[A-Z0-9\-]{6,64}"
            autocomplete="off"
            spellcheck="false"
            aria-describedby="lote-hint"
            required
          >
          <label class="sr-only" for="hash-input"><?php esc_html_e('Hash SHA-256 (opcional)', 'castuo-agritech'); ?></label>
          <input
            type="text"
            id="hash-input"
            class="verify-input"
            placeholder="<?php esc_attr_e('Hash SHA-256 (64 hex, opcional)', 'castuo-agritech'); ?>"
            pattern="[a-fA-F0-9]{64}"
            autocomplete="off"
            spellcheck="false"
            maxlength="64"
          >
          <button type="submit" class="btn-verify" id="verify-btn">
            <?php esc_html_e('Verificar', 'castuo-agritech'); ?>
          </button>
        </form>
        <p id="lote-hint" class="sr-only"><?php esc_html_e('Formato: letras mayúsculas y guiones, entre 6 y 64 caracteres.', 'castuo-agritech'); ?></p>

        <!-- Result area — populated via JS -->
        <div class="verify-result" id="verify-result" role="region" aria-live="polite" aria-label="<?php esc_attr_e('Resultado de verificación', 'castuo-agritech'); ?>">

          <div class="verify-status" id="verify-status-badge" role="status"></div>

          <div class="verify-data" id="verify-data" aria-label="<?php esc_attr_e('Datos del lote', 'castuo-agritech'); ?>"></div>

        </div>
      </div>

    </div>
  </section>
</main>

<?php get_footer(); ?>

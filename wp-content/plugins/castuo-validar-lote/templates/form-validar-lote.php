<?php
/**
 * Template: Formulario Validar Lote
 * Incluido via shortcode [castuo_validar_lote] o page-operador.php
 */
if ( ! defined( 'ABSPATH' ) ) { exit; }
$current_user = wp_get_current_user();
?>
<div id="castuo-validar-lote" class="castuo-form-wrapper">

    <div class="castuo-form-header">
        <h2><?php esc_html_e( 'Validar Lote Agrícola', 'castuo-validar-lote' ); ?></h2>
        <p class="castuo-subtitle">
            <?php esc_html_e( 'Registro inmutable en GaiaChain + Certificado PDF + QR de trazabilidad', 'castuo-validar-lote' ); ?>
        </p>
    </div>

    <form id="castuo-form" novalidate>
        <?php wp_nonce_field( 'castuo_validar_lote', 'castuo_nonce' ); ?>

        <div class="castuo-row">
            <div class="castuo-field castuo-field--required">
                <label for="castuo-lote-id"><?php esc_html_e( 'ID de Lote', 'castuo-validar-lote' ); ?></label>
                <input type="text" id="castuo-lote-id" name="lote_id"
                    placeholder="LOTE-2026-001" minlength="3" maxlength="64" required>
                <span class="castuo-hint"><?php esc_html_e( 'Identificador único del lote (mínimo 3 caracteres)', 'castuo-validar-lote' ); ?></span>
            </div>

            <div class="castuo-field">
                <label for="castuo-cultivo"><?php esc_html_e( 'Cultivo', 'castuo-validar-lote' ); ?></label>
                <select id="castuo-cultivo" name="cultivo">
                    <option value=""><?php esc_html_e( '— Seleccionar —', 'castuo-validar-lote' ); ?></option>
                    <option value="cannabis_medicinal"><?php esc_html_e( 'Cannabis medicinal', 'castuo-validar-lote' ); ?></option>
                    <option value="lechuga"><?php esc_html_e( 'Lechuga', 'castuo-validar-lote' ); ?></option>
                    <option value="tomate"><?php esc_html_e( 'Tomate', 'castuo-validar-lote' ); ?></option>
                    <option value="espinaca"><?php esc_html_e( 'Espinaca', 'castuo-validar-lote' ); ?></option>
                    <option value="otro"><?php esc_html_e( 'Otro', 'castuo-validar-lote' ); ?></option>
                </select>
            </div>
        </div>

        <div class="castuo-row">
            <div class="castuo-field">
                <label for="castuo-humedad"><?php esc_html_e( 'Humedad (%)', 'castuo-validar-lote' ); ?></label>
                <input type="number" id="castuo-humedad" name="humedad_pct"
                    placeholder="12.3" min="0" max="100" step="0.1">
            </div>

            <div class="castuo-field">
                <label for="castuo-thc"><?php esc_html_e( 'THC (%)', 'castuo-validar-lote' ); ?></label>
                <input type="number" id="castuo-thc" name="thc_pct"
                    placeholder="0.18" min="0" max="100" step="0.01">
            </div>

            <div class="castuo-field">
                <label for="castuo-cbd"><?php esc_html_e( 'CBD (%)', 'castuo-validar-lote' ); ?></label>
                <input type="number" id="castuo-cbd" name="cbd_pct"
                    placeholder="8.5" min="0" max="100" step="0.01">
            </div>
        </div>

        <div class="castuo-row">
            <div class="castuo-field">
                <label for="castuo-kg"><?php esc_html_e( 'Kg cosechados', 'castuo-validar-lote' ); ?></label>
                <input type="number" id="castuo-kg" name="kg_cosechados"
                    placeholder="45.2" min="0" step="0.01">
            </div>

            <div class="castuo-field castuo-field--required">
                <label for="castuo-fecha"><?php esc_html_e( 'Fecha de cosecha', 'castuo-validar-lote' ); ?></label>
                <input type="date" id="castuo-fecha" name="fecha_cosecha"
                    value="<?php echo esc_attr( date( 'Y-m-d' ) ); ?>" required>
            </div>
        </div>

        <div class="castuo-field">
            <label for="castuo-ubicacion"><?php esc_html_e( 'Ubicación / Parcela SIGPAC', 'castuo-validar-lote' ); ?></label>
            <input type="text" id="castuo-ubicacion" name="ubicacion"
                placeholder="Dehesa de Cáceres, parcela 42">
        </div>

        <div class="castuo-row castuo-row--meta">
            <div class="castuo-field">
                <label for="castuo-expediente"><?php esc_html_e( 'Expediente AEMPS (opcional)', 'castuo-validar-lote' ); ?></label>
                <input type="text" id="castuo-expediente" name="aemps_expediente"
                    placeholder="EC-2026-XXXX">
            </div>
            <div class="castuo-field castuo-field--checkbox">
                <label>
                    <input type="checkbox" id="castuo-eco" name="eco" value="1">
                    <?php esc_html_e( 'Producción ecológica (Reg. 2018/848)', 'castuo-validar-lote' ); ?>
                </label>
            </div>
        </div>

        <div class="castuo-actions">
            <button type="submit" id="castuo-submit" class="castuo-btn castuo-btn--primary">
                <span class="castuo-btn__label"><?php esc_html_e( 'Validar y Registrar en Blockchain', 'castuo-validar-lote' ); ?></span>
                <span class="castuo-btn__spinner" hidden>⏳</span>
            </button>
        </div>
    </form>

    <!-- Resultado -->
    <div id="castuo-result" class="castuo-result" hidden>
        <div class="castuo-result__status castuo-result__status--ok" hidden>
            <h3>✅ <?php esc_html_e( 'Lote registrado en GaiaChain', 'castuo-validar-lote' ); ?></h3>
        </div>
        <div class="castuo-result__status castuo-result__status--fallback" hidden>
            <h3>⚠️ <?php esc_html_e( 'Registrado en modo simulado (sin GaiaChain)', 'castuo-validar-lote' ); ?></h3>
        </div>
        <table class="castuo-result__table">
            <tr><th><?php esc_html_e( 'Lote ID', 'castuo-validar-lote' ); ?></th><td id="r-lote-id"></td></tr>
            <tr><th><?php esc_html_e( 'TX Hash', 'castuo-validar-lote' ); ?></th><td id="r-tx-hash"><code></code></td></tr>
            <tr><th><?php esc_html_e( 'Blockchain', 'castuo-validar-lote' ); ?></th><td id="r-blockchain"></td></tr>
            <tr><th><?php esc_html_e( 'Generado', 'castuo-validar-lote' ); ?></th><td id="r-fecha"></td></tr>
        </table>
        <div class="castuo-result__actions">
            <a id="r-cert-link" href="#" class="castuo-btn castuo-btn--secondary" target="_blank" hidden>
                📄 <?php esc_html_e( 'Descargar Certificado PDF', 'castuo-validar-lote' ); ?>
            </a>
            <a id="r-qr-link" href="#" class="castuo-btn castuo-btn--secondary" target="_blank" hidden>
                📲 <?php esc_html_e( 'Ver QR de trazabilidad', 'castuo-validar-lote' ); ?>
            </a>
        </div>
    </div>

    <div id="castuo-error" class="castuo-error" hidden></div>

    <!-- Historial (últimos 10 lotes del usuario) -->
    <div class="castuo-history">
        <h3><?php esc_html_e( 'Historial de lotes validados', 'castuo-validar-lote' ); ?></h3>
        <div id="castuo-history-table"></div>
    </div>
</div>

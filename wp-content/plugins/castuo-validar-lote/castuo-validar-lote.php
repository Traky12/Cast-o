<?php
/**
 * Plugin Name: Castúo Validar Lote
 * Plugin URI:  https://castuo360.eu
 * Description: Formulario de validación de lotes agrícolas integrado con CASTÚO-SYSTEM API v3.1.
 *              Registra en GaiaChain y genera certificado PDF + QR inmutable.
 * Version:     1.0.0
 * Author:      Castúo-System™
 * License:     Proprietary
 * Text Domain: castuo-validar-lote
 *
 * Requiere:
 *   - WordPress ≥ 6.4
 *   - PHP ≥ 8.1
 *   - CASTUO_API_URL definido en wp-config.php o como constante
 *   - CASTUO_JWT_SECRET definido en wp-config.php (o se lee desde secreto Vault)
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

// ── Constantes ────────────────────────────────────────────────────────────────
define( 'CASTUO_PLUGIN_VERSION', '1.0.0' );
define( 'CASTUO_PLUGIN_DIR', plugin_dir_path( __FILE__ ) );
define( 'CASTUO_PLUGIN_URL', plugin_dir_url( __FILE__ ) );

if ( ! defined( 'CASTUO_API_URL' ) ) {
    define( 'CASTUO_API_URL', get_option( 'castuo_api_url', 'http://fastapi:8000' ) );
}

// ── Cargar clases ─────────────────────────────────────────────────────────────
require_once CASTUO_PLUGIN_DIR . 'includes/class-castuo-jwt.php';
require_once CASTUO_PLUGIN_DIR . 'includes/class-castuo-api-client.php';
require_once CASTUO_PLUGIN_DIR . 'includes/class-castuo-rest-proxy.php';
require_once CASTUO_PLUGIN_DIR . 'admin/class-castuo-settings.php';

// ── Init ──────────────────────────────────────────────────────────────────────
add_action( 'init', function () {
    load_plugin_textdomain( 'castuo-validar-lote', false, dirname( plugin_basename( __FILE__ ) ) . '/languages' );
} );

add_action( 'wp_enqueue_scripts', function () {
    if ( ! is_page_template( 'page-operador.php' ) && ! has_shortcode( get_post()->post_content ?? '', 'castuo_validar_lote' ) ) {
        return;
    }
    wp_enqueue_style(
        'castuo-validar-lote',
        CASTUO_PLUGIN_URL . 'assets/css/castuo-form.css',
        [],
        CASTUO_PLUGIN_VERSION
    );
    wp_enqueue_script(
        'castuo-validar-lote',
        CASTUO_PLUGIN_URL . 'assets/js/castuo-form.js',
        [ 'jquery' ],
        CASTUO_PLUGIN_VERSION,
        true
    );
    wp_localize_script( 'castuo-validar-lote', 'castuo', [
        'restUrl'  => esc_url_raw( rest_url( 'castuo/v1/validar_lote' ) ),
        'nonce'    => wp_create_nonce( 'wp_rest' ),
        'homeUrl'  => home_url(),
        'version'  => CASTUO_PLUGIN_VERSION,
    ] );
} );

// ── Shortcode [castuo_validar_lote] ───────────────────────────────────────────
add_shortcode( 'castuo_validar_lote', function ( $atts ) {
    if ( ! is_user_logged_in() ) {
        return '<p class="castuo-notice">' .
            esc_html__( 'Debes iniciar sesión para validar lotes.', 'castuo-validar-lote' ) .
            '</p>';
    }
    if ( ! current_user_can( 'edit_posts' ) ) {
        return '<p class="castuo-notice castuo-error">' .
            esc_html__( 'No tienes permiso para acceder a esta función.', 'castuo-validar-lote' ) .
            '</p>';
    }
    ob_start();
    include CASTUO_PLUGIN_DIR . 'templates/form-validar-lote.php';
    return ob_get_clean();
} );

// ── REST API proxy ────────────────────────────────────────────────────────────
add_action( 'rest_api_init', function () {
    $proxy = new Castuo_Rest_Proxy();
    $proxy->register_routes();
} );

// ── Admin settings ────────────────────────────────────────────────────────────
if ( is_admin() ) {
    new Castuo_Settings();
}

<?php
/**
 * CASTÚO Agritech Theme — functions.php
 * Setup, Customizer, REST proxy for QR verification.
 */

defined('ABSPATH') || exit;

// ─── Theme Setup ──────────────────────────────────────────────
add_action('after_setup_theme', function () {
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('html5', ['search-form', 'comment-form', 'gallery', 'caption', 'style', 'script']);
    add_theme_support('custom-logo', [
        'height'      => 40,
        'width'       => 160,
        'flex-width'  => true,
        'flex-height' => true,
    ]);
    register_nav_menus([
        'primary' => __('Primary Menu', 'castuo-agritech'),
        'footer'  => __('Footer Menu', 'castuo-agritech'),
    ]);
    load_theme_textdomain('castuo-agritech', get_template_directory() . '/languages');
});

// ─── Enqueue Assets ───────────────────────────────────────────
add_action('wp_enqueue_scripts', function () {
    $v = wp_get_theme()->get('Version');
    $uri = get_template_directory_uri();

    // Google Fonts (self-hosted equiv via CSS @import avoided — use preconnect)
    wp_enqueue_style('castuo-fonts',
        'https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap',
        [], null
    );
    wp_enqueue_style('castuo-main', get_stylesheet_uri(), ['castuo-fonts'], $v);
    wp_enqueue_script('castuo-main', $uri . '/assets/js/castuo.js', [], $v, true);

    // Pass backend URL to JS (set via Customizer)
    wp_localize_script('castuo-main', 'CASTUO', [
        'api_url'    => esc_url(get_theme_mod('castuo_api_url', 'https://api.castuo360.eu')),
        'verify_url' => rest_url('castuo/v1/verify'),
        'nonce'      => wp_create_nonce('wp_rest'),
    ]);
});

// ─── Customizer ───────────────────────────────────────────────
add_action('customize_register', function (\WP_Customize_Manager $wp_customize) {

    // ── Section: CASTÚO Settings ───────────────────────────────
    $wp_customize->add_section('castuo_settings', [
        'title'    => __('CASTÚO Agritech', 'castuo-agritech'),
        'priority' => 30,
    ]);

    // Hero tagline
    $wp_customize->add_setting('castuo_hero_tagline', [
        'default'           => 'Agricultura inteligente.<br><em>Trazabilidad verificable.</em>',
        'sanitize_callback' => 'wp_kses_post',
    ]);
    $wp_customize->add_control('castuo_hero_tagline', [
        'label'   => __('Hero tagline (HTML permitido)', 'castuo-agritech'),
        'section' => 'castuo_settings',
        'type'    => 'textarea',
    ]);

    // Hero subtitle
    $wp_customize->add_setting('castuo_hero_subtitle', [
        'default'           => 'Microgreens, brotes y flores comestibles cultivados en invernadero agrovoltaico hidropónico. Cada lote trazado en blockchain desde la semilla hasta tu almacén.',
        'sanitize_callback' => 'sanitize_textarea_field',
    ]);
    $wp_customize->add_control('castuo_hero_subtitle', [
        'label'   => __('Hero subtítulo', 'castuo-agritech'),
        'section' => 'castuo_settings',
        'type'    => 'textarea',
    ]);

    // CTA primary
    $wp_customize->add_setting('castuo_cta_text', [
        'default'           => 'Solicitar catálogo B2B',
        'sanitize_callback' => 'sanitize_text_field',
    ]);
    $wp_customize->add_control('castuo_cta_text', [
        'label'   => __('CTA principal texto', 'castuo-agritech'),
        'section' => 'castuo_settings',
        'type'    => 'text',
    ]);

    $wp_customize->add_setting('castuo_cta_url', [
        'default'           => '#contacto',
        'sanitize_callback' => 'esc_url_raw',
    ]);
    $wp_customize->add_control('castuo_cta_url', [
        'label'   => __('CTA principal URL', 'castuo-agritech'),
        'section' => 'castuo_settings',
        'type'    => 'url',
    ]);

    // Backend API URL
    $wp_customize->add_setting('castuo_api_url', [
        'default'           => 'https://api.castuo360.eu',
        'sanitize_callback' => 'esc_url_raw',
    ]);
    $wp_customize->add_control('castuo_api_url', [
        'label'       => __('Backend API URL (FastAPI)', 'castuo-agritech'),
        'description' => __('Endpoint del sistema CASTÚO para verificar trazabilidad QR.', 'castuo-agritech'),
        'section'     => 'castuo_settings',
        'type'        => 'url',
    ]);

    // Contact email
    $wp_customize->add_setting('castuo_contact_email', [
        'default'           => 'b2b@castuo360.eu',
        'sanitize_callback' => 'sanitize_email',
    ]);
    $wp_customize->add_control('castuo_contact_email', [
        'label'   => __('Email de contacto B2B', 'castuo-agritech'),
        'section' => 'castuo_settings',
        'type'    => 'email',
    ]);

    // Min order notice
    $wp_customize->add_setting('castuo_moq_note', [
        'default'           => 'Pedido mínimo 5 kg/variedad. Entrega en cadena de frío 2-8 °C.',
        'sanitize_callback' => 'sanitize_text_field',
    ]);
    $wp_customize->add_control('castuo_moq_note', [
        'label'   => __('Nota pedido mínimo B2B', 'castuo-agritech'),
        'section' => 'castuo_settings',
        'type'    => 'text',
    ]);
});

// ─── REST: QR Verification Proxy ──────────────────────────────
// Avoids CORS issues from browser → backend; sanitizes input.
add_action('rest_api_init', function () {
    register_rest_route('castuo/v1', '/verify', [
        'methods'             => 'GET',
        'callback'            => 'castuo_verify_qr',
        'permission_callback' => '__return_true',
        'args'                => [
            'lote_id' => [
                'required'          => true,
                'sanitize_callback' => 'sanitize_text_field',
                'validate_callback' => function ($v) {
                    return (bool) preg_match('/^[A-Z0-9\-]{6,64}$/', $v);
                },
            ],
            'hash' => [
                'required'          => false,
                'sanitize_callback' => 'sanitize_text_field',
                'validate_callback' => function ($v) {
                    return ! $v || (bool) preg_match('/^[a-fA-F0-9]{64}$/', $v);
                },
            ],
        ],
    ]);
});

function castuo_verify_qr(\WP_REST_Request $request): \WP_REST_Response {
    $lote_id = $request->get_param('lote_id');
    $hash    = $request->get_param('hash') ?: '';
    $api_url = esc_url_raw(get_theme_mod('castuo_api_url', 'https://api.castuo360.eu'));

    // Path: /api/v1/trazabilidad/qr/verificar/{lote_id}/{hash}
    $endpoint = trailingslashit($api_url) . 'api/v1/trazabilidad/qr/verificar/' . rawurlencode($lote_id);
    if ($hash) {
        $endpoint .= '/' . rawurlencode($hash);
    }

    $response = wp_remote_get($endpoint, [
        'timeout' => 10,
        'headers' => ['Accept' => 'application/json'],
    ]);

    if (is_wp_error($response)) {
        return new \WP_REST_Response([
            'valid'   => false,
            'error'   => 'Backend no disponible. Inténtalo de nuevo.',
        ], 503);
    }

    $code = wp_remote_retrieve_response_code($response);
    $body = json_decode(wp_remote_retrieve_body($response), true);

    if ($code !== 200 || ! $body) {
        return new \WP_REST_Response([
            'valid'   => false,
            'error'   => 'Lote no encontrado o hash incorrecto.',
        ], 404);
    }

    return new \WP_REST_Response($body, 200);
}

// ─── Widgets ──────────────────────────────────────────────────
add_action('widgets_init', function () {
    register_sidebar([
        'name'          => __('Footer Widgets', 'castuo-agritech'),
        'id'            => 'footer-1',
        'before_widget' => '<div class="footer-widget">',
        'after_widget'  => '</div>',
        'before_title'  => '<h4 class="widget-title">',
        'after_title'   => '</h4>',
    ]);
});

// ─── Page template loader ──────────────────────────────────────
add_filter('template_include', function ($template) {
    if (is_page()) {
        $tpl = get_post_meta(get_the_ID(), '_wp_page_template', true);
        if ($tpl && $tpl !== 'default') {
            $path = get_template_directory() . '/' . $tpl;
            if (file_exists($path)) return $path;
        }
    }
    return $template;
});

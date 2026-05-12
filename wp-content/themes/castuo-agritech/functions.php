<?php
/**
 * CASTÚO Agritech Theme — functions.php
 * Setup, Customizer, REST proxy for QR verification.
 */

defined('ABSPATH') || exit;

function castuo_page_url(string $slug): string {
    $page = get_page_by_path($slug);
    if ($page instanceof \WP_Post) {
        return get_permalink($page);
    }
    return add_query_arg('pagename', $slug, home_url('/'));
}

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

    // ── Section: Comercial Metrics ───────────────────────────
    $wp_customize->add_section('castuo_commercial_metrics', [
        'title'    => __('Metricas comerciales', 'castuo-agritech'),
        'priority' => 120,
    ]);

    $wp_customize->add_setting('castuo_tam_value', [
        'default'           => 'EUR 16.96B',
        'sanitize_callback' => 'sanitize_text_field',
    ]);
    $wp_customize->add_control('castuo_tam_value', [
        'label'   => __('TAM', 'castuo-agritech'),
        'section' => 'castuo_commercial_metrics',
        'type'    => 'text',
    ]);

    $wp_customize->add_setting('castuo_sam_value', [
        'default'           => 'EUR 2.40B',
        'sanitize_callback' => 'sanitize_text_field',
    ]);
    $wp_customize->add_control('castuo_sam_value', [
        'label'   => __('SAM', 'castuo-agritech'),
        'section' => 'castuo_commercial_metrics',
        'type'    => 'text',
    ]);

    $wp_customize->add_setting('castuo_som_value', [
        'default'           => 'EUR 120M',
        'sanitize_callback' => 'sanitize_text_field',
    ]);
    $wp_customize->add_control('castuo_som_value', [
        'label'   => __('SOM / ARR objetivo', 'castuo-agritech'),
        'section' => 'castuo_commercial_metrics',
        'type'    => 'text',
    ]);

    $wp_customize->add_setting('castuo_farms_target', [
        'default'           => '1.012 farms',
        'sanitize_callback' => 'sanitize_text_field',
    ]);
    $wp_customize->add_control('castuo_farms_target', [
        'label'   => __('Objetivo farms', 'castuo-agritech'),
        'section' => 'castuo_commercial_metrics',
        'type'    => 'text',
    ]);

    // ── Section: Compliance Blocks ───────────────────────────
    $wp_customize->add_section('castuo_compliance_blocks', [
        'title'    => __('Bloques de cumplimiento', 'castuo-agritech'),
        'priority' => 130,
    ]);

    $wp_customize->add_setting('castuo_rgpd_summary', [
        'default'           => '100% compliant con RGPD Art. 30 y gobernanza de datos trazable.',
        'sanitize_callback' => 'sanitize_textarea_field',
    ]);
    $wp_customize->add_control('castuo_rgpd_summary', [
        'label'   => __('Resumen RGPD', 'castuo-agritech'),
        'section' => 'castuo_compliance_blocks',
        'type'    => 'textarea',
    ]);

    $wp_customize->add_setting('castuo_iso_summary', [
        'default'           => 'Controles ISO 27001 con auditoria operativa y revisiones periodicas de acceso.',
        'sanitize_callback' => 'sanitize_textarea_field',
    ]);
    $wp_customize->add_control('castuo_iso_summary', [
        'label'   => __('Resumen ISO 27001', 'castuo-agritech'),
        'section' => 'castuo_compliance_blocks',
        'type'    => 'textarea',
    ]);

    $wp_customize->add_setting('castuo_ai_act_summary', [
        'default'           => 'Human-in-the-loop en decisiones criticas y trazabilidad completa de inferencias.',
        'sanitize_callback' => 'sanitize_textarea_field',
    ]);
    $wp_customize->add_control('castuo_ai_act_summary', [
        'label'   => __('Resumen AI Act', 'castuo-agritech'),
        'section' => 'castuo_compliance_blocks',
        'type'    => 'textarea',
    ]);

    $wp_customize->add_setting('castuo_nis2_cra_summary', [
        'default'           => 'NIS2 + CRA con runbooks de incidentes, observabilidad y politicas CI/CD seguras.',
        'sanitize_callback' => 'sanitize_textarea_field',
    ]);
    $wp_customize->add_control('castuo_nis2_cra_summary', [
        'label'   => __('Resumen NIS2 / CRA', 'castuo-agritech'),
        'section' => 'castuo_compliance_blocks',
        'type'    => 'textarea',
    ]);
});

// ─── CPT: Roadmap Hitos ──────────────────────────────────────
add_action('init', function () {
    $labels = [
        'name'               => __('Hitos Roadmap', 'castuo-agritech'),
        'singular_name'      => __('Hito', 'castuo-agritech'),
        'menu_name'          => __('Roadmap', 'castuo-agritech'),
        'add_new'            => __('Nuevo hito', 'castuo-agritech'),
        'add_new_item'       => __('Crear hito de roadmap', 'castuo-agritech'),
        'edit_item'          => __('Editar hito', 'castuo-agritech'),
        'new_item'           => __('Nuevo hito', 'castuo-agritech'),
        'view_item'          => __('Ver hito', 'castuo-agritech'),
        'search_items'       => __('Buscar hitos', 'castuo-agritech'),
        'not_found'          => __('No hay hitos', 'castuo-agritech'),
        'not_found_in_trash' => __('No hay hitos en papelera', 'castuo-agritech'),
    ];

    register_post_type('roadmap_hit', [
        'labels'             => $labels,
        'public'             => true,
        'show_in_rest'       => true,
        'menu_position'      => 21,
        'menu_icon'          => 'dashicons-chart-line',
        'supports'           => ['title', 'editor', 'excerpt'],
        'has_archive'        => false,
        'rewrite'            => ['slug' => 'roadmap-hitos'],
    ]);
});

add_action('add_meta_boxes', function () {
    add_meta_box(
        'castuo_roadmap_meta',
        __('Datos de hito', 'castuo-agritech'),
        function (\WP_Post $post) {
            wp_nonce_field('castuo_roadmap_meta_nonce', 'castuo_roadmap_meta_nonce');
            $quarter = get_post_meta($post->ID, 'quarter', true);
            $status = get_post_meta($post->ID, 'status', true);
            echo '<p><label for="castuo_quarter"><strong>' . esc_html__('Trimestre', 'castuo-agritech') . '</strong></label><br>';
            echo '<input type="text" id="castuo_quarter" name="castuo_quarter" value="' . esc_attr($quarter) . '" placeholder="Q2 2026" style="width:100%"></p>';
            echo '<p><label for="castuo_status"><strong>' . esc_html__('Estado', 'castuo-agritech') . '</strong></label><br>';
            echo '<select id="castuo_status" name="castuo_status" style="width:100%">';
            $statuses = [
                'planned' => __('Planificado', 'castuo-agritech'),
                'in_progress' => __('En progreso', 'castuo-agritech'),
                'done' => __('Completado', 'castuo-agritech'),
            ];
            foreach ($statuses as $key => $label) {
                $selected = selected($status, $key, false);
                echo '<option value="' . esc_attr($key) . '" ' . $selected . '>' . esc_html($label) . '</option>';
            }
            echo '</select></p>';
        },
        'roadmap_hit',
        'side',
        'default'
    );
});

add_action('save_post_roadmap_hit', function (int $post_id): void {
    if (! isset($_POST['castuo_roadmap_meta_nonce']) || ! wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['castuo_roadmap_meta_nonce'])), 'castuo_roadmap_meta_nonce')) {
        return;
    }
    if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) {
        return;
    }
    if (! current_user_can('edit_post', $post_id)) {
        return;
    }

    $quarter = isset($_POST['castuo_quarter']) ? sanitize_text_field(wp_unslash($_POST['castuo_quarter'])) : '';
    $status = isset($_POST['castuo_status']) ? sanitize_key(wp_unslash($_POST['castuo_status'])) : 'planned';

    update_post_meta($post_id, 'quarter', $quarter);
    update_post_meta($post_id, 'status', in_array($status, ['planned', 'in_progress', 'done'], true) ? $status : 'planned');
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

// ─── Bootstrap de contenido inicial ──────────────────────────
add_action('after_switch_theme', function () {
    $pages = [
        [
            'title'   => 'Inicio',
            'slug'    => 'inicio',
            'content' => 'Landing principal CASTUO.',
            'template'=> 'front-page.php',
        ],
        [
            'title'   => 'Verificar',
            'slug'    => 'verificar',
            'content' => 'Verificacion de trazabilidad de lotes.',
            'template'=> 'page-trazabilidad.php',
        ],
        [
            'title'   => 'Sistema',
            'slug'    => 'sistema',
            'content' => 'Arquitectura, cumplimiento y operacion de CASTUO-SYSTEM.',
            'template'=> 'page-sistema.php',
        ],
        [
            'title'   => 'Roadmap',
            'slug'    => 'roadmap',
            'content' => 'Hitos operativos y de producto de CASTUO-SYSTEM.',
            'template'=> 'page-roadmap.php',
        ],
    ];

    foreach ($pages as $cfg) {
        $existing = get_page_by_path($cfg['slug']);
        if ($existing instanceof \WP_Post) {
            continue;
        }

        $id = wp_insert_post([
            'post_title'   => $cfg['title'],
            'post_name'    => $cfg['slug'],
            'post_content' => $cfg['content'],
            'post_status'  => 'publish',
            'post_type'    => 'page',
        ]);

        if (! is_wp_error($id) && $id) {
            update_post_meta($id, '_wp_page_template', $cfg['template']);
        }
    }

    $home = get_page_by_path('inicio');
    if ($home instanceof \WP_Post) {
        update_option('show_on_front', 'page');
        update_option('page_on_front', (int) $home->ID);
    }

    $default_hits = [
        [
            'title' => 'Q2 2026 - Customizer comercial',
            'content' => 'Panel editable para metricas de mercado y bloques de cumplimiento en la pagina Sistema.',
            'quarter' => 'Q2 2026',
            'status' => 'in_progress',
        ],
        [
            'title' => 'Q3 2026 - Roadmap dinamico',
            'content' => 'Gestion de hitos como contenido editable sin tocar codigo, con estado por trimestre.',
            'quarter' => 'Q3 2026',
            'status' => 'planned',
        ],
        [
            'title' => 'Q4 2026 - Integracion documental eIDAS',
            'content' => 'Firma y trazabilidad de certificados operativos con evidencia verificable.',
            'quarter' => 'Q4 2026',
            'status' => 'planned',
        ],
    ];

    foreach ($default_hits as $hit) {
        $exists = get_page_by_title($hit['title'], OBJECT, 'roadmap_hit');
        if ($exists instanceof \WP_Post) {
            continue;
        }
        $id = wp_insert_post([
            'post_type' => 'roadmap_hit',
            'post_title' => $hit['title'],
            'post_content' => $hit['content'],
            'post_status' => 'publish',
        ]);
        if (! is_wp_error($id) && $id) {
            update_post_meta($id, 'quarter', $hit['quarter']);
            update_post_meta($id, 'status', $hit['status']);
        }
    }
});

<?php
/**
 * Página de ajustes del plugin CASTÚO Validar Lote
 * Accesible desde: Ajustes → CASTÚO API
 */
class Castuo_Settings {

    const OPTION_GROUP = 'castuo_settings_group';
    const PAGE_SLUG    = 'castuo-api-settings';

    public function __construct() {
        add_action( 'admin_menu',       [ $this, 'add_menu_page' ] );
        add_action( 'admin_init',       [ $this, 'register_settings' ] );
        add_action( 'admin_notices',    [ $this, 'maybe_show_notice' ] );
    }

    public function add_menu_page(): void {
        add_options_page(
            __( 'CASTÚO API', 'castuo-validar-lote' ),
            __( 'CASTÚO API', 'castuo-validar-lote' ),
            'manage_options',
            self::PAGE_SLUG,
            [ $this, 'render_page' ]
        );
    }

    public function register_settings(): void {
        register_setting( self::OPTION_GROUP, 'castuo_api_url',    [ 'sanitize_callback' => 'esc_url_raw',       'default' => 'http://fastapi:8000' ] );
        register_setting( self::OPTION_GROUP, 'castuo_jwt_secret', [ 'sanitize_callback' => 'sanitize_text_field', 'default' => '' ] );
        register_setting( self::OPTION_GROUP, 'castuo_verify_base_url', [ 'sanitize_callback' => 'esc_url_raw', 'default' => 'https://verify.castuo360.eu/lote' ] );
        register_setting( self::OPTION_GROUP, 'castuo_debug_mode', [ 'sanitize_callback' => 'absint',            'default' => 0 ] );

        // ── Sección principal ────────────────────────────────────────────────
        add_settings_section(
            'castuo_main',
            __( 'Conexión con CASTÚO API', 'castuo-validar-lote' ),
            function () {
                echo '<p>' . esc_html__( 'Configura la conexión con el backend CASTÚO-SYSTEM™ v3.1.', 'castuo-validar-lote' ) . '</p>';
            },
            self::PAGE_SLUG
        );

        add_settings_field( 'castuo_api_url', __( 'URL de la API', 'castuo-validar-lote' ),
            [ $this, 'render_url_field' ], self::PAGE_SLUG, 'castuo_main',
            [ 'label_for' => 'castuo_api_url', 'description' => __( 'Ej: https://api.castuo-system.cloud o http://fastapi:8000 en Docker.', 'castuo-validar-lote' ) ]
        );

        add_settings_field( 'castuo_jwt_secret', __( 'JWT Secret', 'castuo-validar-lote' ),
            [ $this, 'render_password_field' ], self::PAGE_SLUG, 'castuo_main',
            [ 'label_for' => 'castuo_jwt_secret', 'description' => __( 'Mismo valor que JWT_SECRET en el backend. Genera uno con: openssl rand -hex 32', 'castuo-validar-lote' ) ]
        );

        add_settings_field( 'castuo_verify_base_url', __( 'URL Base para QR', 'castuo-validar-lote' ),
            [ $this, 'render_url_field' ], self::PAGE_SLUG, 'castuo_main',
            [ 'label_for' => 'castuo_verify_base_url', 'description' => __( 'Se añade /{lote_id} en el QR de trazabilidad.', 'castuo-validar-lote' ) ]
        );

        // ── Sección avanzada ─────────────────────────────────────────────────
        add_settings_section(
            'castuo_advanced',
            __( 'Opciones Avanzadas', 'castuo-validar-lote' ),
            null,
            self::PAGE_SLUG
        );

        add_settings_field( 'castuo_debug_mode', __( 'Modo Debug', 'castuo-validar-lote' ),
            [ $this, 'render_checkbox_field' ], self::PAGE_SLUG, 'castuo_advanced',
            [ 'label_for' => 'castuo_debug_mode', 'description' => __( 'Activa logs detallados en la consola del navegador (solo desarrollo).', 'castuo-validar-lote' ) ]
        );
    }

    public function render_page(): void {
        if ( ! current_user_can( 'manage_options' ) ) {
            return;
        }
        $health = $this->check_api_health();
        ?>
        <div class="wrap">
            <h1><?php echo esc_html( get_admin_page_title() ); ?></h1>

            <!-- Estado de la API -->
            <div class="castuo-admin-status" style="margin:16px 0;padding:12px 16px;border-radius:4px;
                background:<?php echo $health['ok'] ? '#edfaed' : '#fce8e8'; ?>;
                border-left:4px solid <?php echo $health['ok'] ? '#2e7d32' : '#c62828'; ?>;">
                <strong><?php echo $health['ok'] ? '✅' : '❌'; ?>
                    <?php esc_html_e( 'CASTÚO API:', 'castuo-validar-lote' ); ?>
                </strong>
                <?php echo esc_html( $health['message'] ); ?>
                <?php if ( $health['ok'] && ! empty( $health['chain_status'] ) ) : ?>
                    &nbsp;|&nbsp; chain: <code><?php echo esc_html( $health['chain_status'] ); ?></code>
                    &nbsp;|&nbsp; v<code><?php echo esc_html( $health['version'] ?? '?' ); ?></code>
                <?php endif; ?>
            </div>

            <form method="post" action="options.php">
                <?php
                settings_fields( self::OPTION_GROUP );
                do_settings_sections( self::PAGE_SLUG );
                submit_button( __( 'Guardar ajustes', 'castuo-validar-lote' ) );
                ?>
            </form>

            <!-- Shortcode helper -->
            <hr>
            <h2><?php esc_html_e( 'Uso del Shortcode', 'castuo-validar-lote' ); ?></h2>
            <p><?php esc_html_e( 'Añade el siguiente shortcode en cualquier página para mostrar el formulario de validación:', 'castuo-validar-lote' ); ?></p>
            <code style="font-size:1.1em;padding:8px 12px;background:#f5f5f5;display:inline-block;border-radius:4px;">
                [castuo_validar_lote]
            </code>

            <h2 style="margin-top:24px;"><?php esc_html_e( 'Test rápido', 'castuo-validar-lote' ); ?></h2>
            <p>
                <a href="<?php echo esc_url( rest_url( 'castuo/v1/health' ) ); ?>" target="_blank" class="button">
                    <?php esc_html_e( 'Probar conexión API', 'castuo-validar-lote' ); ?>
                </a>
            </p>
        </div>
        <?php
    }

    // ── Field renderers ───────────────────────────────────────────────────────

    public function render_url_field( array $args ): void {
        $id  = $args['label_for'];
        $val = get_option( $id, '' );
        printf(
            '<input type="url" id="%s" name="%s" value="%s" class="regular-text" placeholder="https://...">',
            esc_attr( $id ), esc_attr( $id ), esc_attr( $val )
        );
        if ( ! empty( $args['description'] ) ) {
            echo '<p class="description">' . esc_html( $args['description'] ) . '</p>';
        }
    }

    public function render_password_field( array $args ): void {
        $id  = $args['label_for'];
        $val = get_option( $id, '' );
        printf(
            '<input type="password" id="%s" name="%s" value="%s" class="regular-text" autocomplete="new-password">',
            esc_attr( $id ), esc_attr( $id ), esc_attr( $val )
        );
        if ( ! empty( $args['description'] ) ) {
            echo '<p class="description">' . esc_html( $args['description'] ) . '</p>';
        }
    }

    public function render_checkbox_field( array $args ): void {
        $id  = $args['label_for'];
        $val = get_option( $id, 0 );
        printf(
            '<input type="checkbox" id="%s" name="%s" value="1" %s>',
            esc_attr( $id ), esc_attr( $id ), checked( 1, $val, false )
        );
        if ( ! empty( $args['description'] ) ) {
            echo '<label for="' . esc_attr( $id ) . '"> ' . esc_html( $args['description'] ) . '</label>';
        }
    }

    // ── API health check ──────────────────────────────────────────────────────

    private function check_api_health(): array {
        $url = trailingslashit( get_option( 'castuo_api_url', '' ) ) . 'health';
        if ( empty( get_option( 'castuo_api_url', '' ) ) ) {
            return [ 'ok' => false, 'message' => __( 'URL de la API no configurada.', 'castuo-validar-lote' ) ];
        }

        $response = wp_remote_get( $url, [ 'timeout' => 5 ] );
        if ( is_wp_error( $response ) ) {
            return [ 'ok' => false, 'message' => $response->get_error_message() ];
        }

        $code = wp_remote_retrieve_response_code( $response );
        $body = json_decode( wp_remote_retrieve_body( $response ), true );

        if ( $code === 200 && ( $body['status'] ?? '' ) === 'ok' ) {
            return [
                'ok'           => true,
                'message'      => __( 'Conectado correctamente.', 'castuo-validar-lote' ),
                'chain_status' => $body['chain_status'] ?? '?',
                'version'      => $body['version'] ?? '?',
            ];
        }

        return [ 'ok' => false, 'message' => sprintf( __( 'Error HTTP %d', 'castuo-validar-lote' ), $code ) ];
    }

    // ── Admin notice tras guardar ─────────────────────────────────────────────

    public function maybe_show_notice(): void {
        if ( ! isset( $_GET['settings-updated'] ) ) {
            return;
        }
        $screen = get_current_screen();
        if ( ! $screen || strpos( $screen->id, self::PAGE_SLUG ) === false ) {
            return;
        }
        echo '<div class="notice notice-success is-dismissible"><p>' .
             esc_html__( 'Ajustes de CASTÚO API guardados.', 'castuo-validar-lote' ) .
             '</p></div>';
    }
}

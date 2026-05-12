<?php
/**
 * REST Proxy: WordPress → CASTÚO FastAPI
 * Endpoint: POST /wp-json/castuo/v1/validar_lote
 *
 * Requiere usuario WordPress con rol editor/admin.
 * Genera JWT firmado con CASTUO_JWT_SECRET y reenvía al backend.
 */
class Castuo_Rest_Proxy {

    public function register_routes(): void {
        register_rest_route( 'castuo/v1', '/validar_lote', [
            'methods'             => 'POST',
            'callback'            => [ $this, 'handle_validar_lote' ],
            'permission_callback' => [ $this, 'check_permission' ],
            'args'                => $this->get_args(),
        ] );

        register_rest_route( 'castuo/v1', '/health', [
            'methods'             => 'GET',
            'callback'            => [ $this, 'handle_health' ],
            'permission_callback' => '__return_true',
        ] );
    }

    public function check_permission( \WP_REST_Request $request ): bool|\WP_Error {
        if ( ! is_user_logged_in() ) {
            return new \WP_Error( 'rest_forbidden', 'Autenticación requerida.', [ 'status' => 401 ] );
        }
        if ( ! current_user_can( 'edit_posts' ) ) {
            return new \WP_Error( 'rest_forbidden', 'Rol insuficiente.', [ 'status' => 403 ] );
        }
        return true;
    }

    public function handle_validar_lote( \WP_REST_Request $request ): \WP_REST_Response|\WP_Error {
        $user    = wp_get_current_user();
        $role    = in_array( 'administrator', $user->roles, true ) ? 'admin' : 'editor';
        $jwt     = Castuo_JWT::generate( $user->user_login, $role );

        $lote_id   = sanitize_text_field( $request->get_param( 'lote_id' ) );
        $metadatos = $request->get_param( 'metadatos' ) ?: [];
        $metadatos['_operador_wp'] = $user->user_login;

        $payload = wp_json_encode( [
            'lote_id'          => $lote_id,
            'metadatos'        => $metadatos,
            'firma_digital'    => $request->get_param( 'firma_digital' ),
            'verify_base_url'  => home_url( '/verificar-lote' ),
        ] );

        $api_url = trailingslashit( CASTUO_API_URL ) . 'api/v1/skills/validar_lote';

        $response = wp_remote_post( $api_url, [
            'headers' => [
                'Content-Type'  => 'application/json',
                'Authorization' => 'Bearer ' . $jwt,
            ],
            'body'    => $payload,
            'timeout' => 30,
        ] );

        if ( is_wp_error( $response ) ) {
            return new \WP_Error(
                'castuo_api_error',
                $response->get_error_message(),
                [ 'status' => 502 ]
            );
        }

        $code = wp_remote_retrieve_response_code( $response );
        $body = json_decode( wp_remote_retrieve_body( $response ), true );

        if ( $code !== 200 ) {
            return new \WP_Error(
                'castuo_api_error',
                $body['detail'] ?? 'Error en CASTÚO API',
                [ 'status' => $code ]
            );
        }

        // Guardar en historial del usuario (últimos 20 lotes)
        $this->save_to_history( $user->ID, $body );

        return new \WP_REST_Response( $body, 200 );
    }

    public function handle_health( \WP_REST_Request $request ): \WP_REST_Response {
        $api_url  = trailingslashit( CASTUO_API_URL ) . 'health';
        $response = wp_remote_get( $api_url, [ 'timeout' => 5 ] );

        if ( is_wp_error( $response ) ) {
            return new \WP_REST_Response( [ 'status' => 'unreachable', 'error' => $response->get_error_message() ], 503 );
        }

        $body = json_decode( wp_remote_retrieve_body( $response ), true );
        return new \WP_REST_Response( $body, wp_remote_retrieve_response_code( $response ) );
    }

    private function save_to_history( int $user_id, array $data ): void {
        $history = get_user_meta( $user_id, 'castuo_lote_history', true ) ?: [];
        array_unshift( $history, [
            'lote_id'         => $data['lote_id'] ?? '',
            'tx_hash'         => $data['tx_hash'] ?? '',
            'status'          => $data['status'] ?? '',
            'blockchain'      => $data['blockchain'] ?? '',
            'certificado_path'=> $data['certificado_path'] ?? '',
            'generado_en'     => $data['generado_en'] ?? '',
        ] );
        update_user_meta( $user_id, 'castuo_lote_history', array_slice( $history, 0, 20 ) );
    }

    private function get_args(): array {
        return [
            'lote_id' => [
                'required'          => true,
                'type'              => 'string',
                'sanitize_callback' => 'sanitize_text_field',
                'validate_callback' => function ( $v ) { return strlen( $v ) >= 3; },
            ],
            'metadatos' => [
                'required' => false,
                'type'     => 'object',
                'default'  => [],
            ],
            'firma_digital' => [
                'required' => false,
                'type'     => 'string',
                'default'  => null,
            ],
        ];
    }
}

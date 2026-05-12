<?php
/**
 * Generador JWT mínimo para WordPress → CASTÚO API
 * HS256 puro (sin dependencias externas)
 */
class Castuo_JWT {

    public static function generate( string $sub, string $role, int $ttl = 3600 ): string {
        $secret = defined( 'CASTUO_JWT_SECRET' ) ? CASTUO_JWT_SECRET : get_option( 'castuo_jwt_secret', '' );
        if ( ! $secret ) {
            // Sin secreto configurado: el backend FastAPI lo acepta en modo dev
            $secret = 'dev-no-secret';
        }

        $header  = self::base64url( json_encode( [ 'alg' => 'HS256', 'typ' => 'JWT' ] ) );
        $payload = self::base64url( json_encode( [
            'sub'  => $sub,
            'role' => $role,
            'iat'  => time(),
            'exp'  => time() + $ttl,
            'iss'  => 'castuo-wordpress',
        ] ) );
        $sig = self::base64url( hash_hmac( 'sha256', "$header.$payload", $secret, true ) );
        return "$header.$payload.$sig";
    }

    private static function base64url( string $data ): string {
        return rtrim( strtr( base64_encode( $data ), '+/', '-_' ), '=' );
    }
}

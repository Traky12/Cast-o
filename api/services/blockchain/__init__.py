from pkgutil import extend_path

# Habilita paquete distribuido entre api/services/blockchain y services/blockchain.
__path__ = extend_path(__path__, __name__)

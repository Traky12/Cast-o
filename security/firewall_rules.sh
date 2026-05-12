#!/bin/bash
# CASTUO 5.0 — Firewall default-deny (ISO 27033, NIST SP 800-41)
# Ejecutar con privilegios (sudo). Ajustar redes según despliegue.

IPTABLES="${IPTABLES:-/sbin/iptables}"

# Políticas por defecto: DENEGAR TODO
$IPTABLES -P INPUT DROP
$IPTABLES -P FORWARD DROP
$IPTABLES -P OUTPUT DROP

# Tráfico local
$IPTABLES -A INPUT -i lo -j ACCEPT
$IPTABLES -A OUTPUT -o lo -j ACCEPT

# SSH solo desde red autorizada (ajustar 192.168.1.0/24)
$IPTABLES -A INPUT -p tcp --dport 22 -s 192.168.1.0/24 -j ACCEPT

# VPN Tailscale (UDP 41641 típico; ajustar si se usa otro)
$IPTABLES -A INPUT -p udp --dport 41641 -j ACCEPT
$IPTABLES -A INPUT -p udp --dport 500 -j ACCEPT
$IPTABLES -A INPUT -p udp --dport 4500 -j ACCEPT

# LoRaWAN (puerto 1700)
$IPTABLES -A INPUT -p udp --dport 1700 -j ACCEPT

# GaiaChain / RPC (ejemplo 8545; solo red interna)
$IPTABLES -A OUTPUT -p tcp --dport 8545 -d 10.0.0.0/8 -j ACCEPT

# ICMP (ping) limitado
$IPTABLES -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s -j ACCEPT

# Conexiones establecidas/relacionadas
$IPTABLES -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
$IPTABLES -A OUTPUT -m conntrack --ctstate ESTABLISHED -j ACCEPT

# Log de intentos denegados (rate limit)
$IPTABLES -A INPUT -m limit --limit 5/min -j LOG --log-prefix "IPTABLES DROPPED: " --log-level 4
$IPTABLES -A INPUT -j DROP

echo "Firewall CASTUO configurado (default-deny)."

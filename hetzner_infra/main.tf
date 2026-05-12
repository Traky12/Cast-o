terraform {
  required_version = ">= 1.5.0"

  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.40"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "hcloud" {
  token = var.hcloud_token
}

# Primary CASTUO computation node
resource "hcloud_server" "castuo_node" {
  name        = var.server_name
  image       = "ubuntu-22.04"
  server_type = var.server_type
  location    = var.location
  ssh_keys    = [var.ssh_key_id]
  public_net {
    ipv4_enabled = true
    ipv6_enabled = true
  }

  user_data = file("${path.module}/user_data.yaml")

  labels = {
    environment = "production"
    component   = "castuo-compute"
    managed-by  = "terraform"
  }

  depends_on = [hcloud_ssh_key.castuo]
}

# SSH key for server access (reference existing key by ID)
resource "hcloud_ssh_key" "castuo" {
  name       = "${var.server_name}-key"
  public_key = file(var.ssh_public_key_path)
  labels = {
    environment = "production"
  }
}

# Data volume for persistent data
resource "hcloud_volume" "castuo_data" {
  name              = "${var.server_name}-data"
  size              = var.volume_size
  location          = var.location
  format            = "ext4"
  delete_protection = true

  labels = {
    environment = "production"
    component   = "storage"
  }
}

# Attach volume to server
resource "hcloud_volume_attachment" "castuo_data" {
  volume_id = hcloud_volume.castuo_data.id
  server_id = hcloud_server.castuo_node.id
  automount = true
}

# Firewall for network security
resource "hcloud_firewall" "castuo" {
  name = "${var.server_name}-fw"
  labels = {
    environment = "production"
  }

  rule {
    direction = "in"
    source_ips = [
      "0.0.0.0/0",
      "::/0",
    ]
    protocol = "tcp"
    port     = "22"
  }

  rule {
    direction = "in"
    source_ips = [
      "0.0.0.0/0",
      "::/0",
    ]
    protocol = "tcp"
    port     = "80"
  }

  rule {
    direction = "in"
    source_ips = [
      "0.0.0.0/0",
      "::/0",
    ]
    protocol = "tcp"
    port     = "443"
  }

  # API SABIONDA (FastAPI)
  rule {
    direction = "in"
    source_ips = ["0.0.0.0/0", "::/0"]
    protocol  = "tcp"
    port      = "8000"
  }

  # n8n workflows — puerto nativo 5678 (NO usar 5432, ese es PostgreSQL)
  rule {
    direction = "in"
    source_ips = ["0.0.0.0/0", "::/0"]
    protocol  = "tcp"
    port      = "5678"
  }

  # Grafana dashboards
  rule {
    direction = "in"
    source_ips = ["0.0.0.0/0", "::/0"]
    protocol  = "tcp"
    port      = "3000"
  }

  # Prometheus (restringir a IPs conocidas en produccion)
  rule {
    direction = "in"
    source_ips = ["0.0.0.0/0", "::/0"]
    protocol  = "tcp"
    port      = "9090"
  }

  # GaiaChain RPC (blockchain interna)
  rule {
    direction = "in"
    source_ips = ["0.0.0.0/0", "::/0"]
    protocol  = "tcp"
    port      = "8545"
  }

  # NOTA SEGURIDAD: Puerto 3306 (MySQL) NO incluido — no hay MySQL en el stack.
  # NOTA SEGURIDAD: Puerto 5432 (PostgreSQL) NO expuesto — solo acceso interno Docker.
  # NOTA SEGURIDAD: Puerto 6443 (k3s API) eliminado — exponer Kubernetes API es riesgo alto.
}

# Apply firewall to server
resource "hcloud_firewall_attachment" "castuo" {
  firewall_id = hcloud_firewall.castuo.id
  server_ids  = [hcloud_server.castuo_node.id]
}

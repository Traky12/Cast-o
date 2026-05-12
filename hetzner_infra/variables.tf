variable "hcloud_token" {
  description = "Hetzner Cloud API token (set via TF_VAR_hcloud_token or in terraform.tfvars)"
  type        = string
  sensitive   = true
}

variable "ssh_key_id" {
  description = "Hetzner Cloud SSH Key ID (retrieve via: hcloud ssh-key list)"
  type        = number
  sensitive   = false
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key file for server access (e.g., ~/.ssh/id_rsa.pub)"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "server_name" {
  description = "Name for the CASTUO compute server"
  type        = string
  default     = "ubuntu-8gb-hel1-1"
}

variable "server_type" {
  description = "Hetzner Cloud server type — produccion: cax21 (ARM64 Ampere, 4vCPU/8GB/40GB, hel1)"
  type        = string
  default     = "cax21"
}

variable "location" {
  description = "Hetzner Cloud datacenter location (fsn1, nbg1, hel1, etc.)"
  type        = string
  default     = "hel1"
}

variable "volume_size" {
  description = "Size of data volume in GB"
  type        = number
  default     = 50
  validation {
    condition     = var.volume_size >= 10
    error_message = "Volume size must be at least 10 GB."
  }
}

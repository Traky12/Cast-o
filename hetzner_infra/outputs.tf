output "server_ip" {
  description = "Public IPv4 address of CASTUO compute node"
  value       = hcloud_server.castuo_node.ipv4_address
  sensitive   = false
}

output "server_ipv6" {
  description = "Public IPv6 address of CASTUO compute node"
  value       = hcloud_server.castuo_node.ipv6_address
  sensitive   = false
}

output "server_id" {
  description = "Hetzner Cloud Server ID"
  value       = hcloud_server.castuo_node.id
  sensitive   = false
}

output "volume_id" {
  description = "Data volume ID"
  value       = hcloud_volume.castuo_data.id
  sensitive   = false
}

output "kubeconfig_location" {
  description = "Location of kubeconfig after deployment"
  value       = "/root/.kube/config"
}

output "n8n_url" {
  description = "n8n automation platform access URL"
  value       = "http://${hcloud_server.castuo_node.ipv4_address}:5678"
}

output "prometheus_url" {
  description = "Prometheus monitoring dashboard URL"
  value       = "http://${hcloud_server.castuo_node.ipv4_address}:9090"
}

output "deployment_info" {
  description = "Deployment summary"
  value = {
    server_name = var.server_name
    server_ip   = hcloud_server.castuo_node.ipv4_address
    server_type = var.server_type
    location    = var.location
    volume_size = var.volume_size
    k3s_cluster = "Ready (via cloud-init)"
    next_steps = [
      "Get kubeconfig: ssh root@${hcloud_server.castuo_node.ipv4_address} cat ~/.kube/config",
      "Access n8n: http://${hcloud_server.castuo_node.ipv4_address}:5678",
      "Monitor: http://${hcloud_server.castuo_node.ipv4_address}:9090"
    ]
  }
}

# Automatización de RPis (Ansible)

Escalar a 10K farms con RPis gestionadas como código. Inventario por región (EU, LATAM, Asia); playbook instala Docker y despliega `rpi-hidroponia` con variables por región.

## Estructura

- `ansible/inventory.ini` — hosts por grupo (rpis_eu, rpis_latam, rpis_asia).
- `ansible/playbook.yml` — instala Docker, despliega plantilla docker-compose.
- `ansible/templates/docker-compose.rpi.yml` — servicio rpi-hidroponia (SENSOR_LIMIT=500, MQTT_QOS=1, REGION).
- `kubernetes/rpi-cluster.yaml` — ejemplo de Application ArgoCD (opcional; para repos con manifiestos K8s).

## Ejecutar el playbook

Desde la raíz del proyecto:

```bash
cd rpi-automation/ansible
ansible-playbook -i inventory.ini playbook.yml --ask-become-pass
```

Te pedirá la contraseña de sudo de las RPis (por defecto en Raspberry Pi OS: `raspberry`; cámbiala por seguridad).

Por región:

```bash
ansible-playbook -i inventory.ini playbook.yml -l rpis_eu -e region=eu --ask-become-pass
ansible-playbook -i inventory.ini playbook.yml -l rpis_latam -e region=latam --ask-become-pass
ansible-playbook -i inventory.ini playbook.yml -l rpis_asia -e region=asia --ask-become-pass
```

Requisitos: Ansible 2.9+, acceso SSH a las RPis (`ansible_user=pi` en `inventory.ini`). Ajustar `ansible_host` a las IPs reales.

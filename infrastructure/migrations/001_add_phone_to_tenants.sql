-- Migration: Add phone contact fields to tenants for WhatsApp alerts
-- Date: 2026-04-03
-- Description: Agrega campos de teléfono para configurar alertas WhatsApp por tenant

-- 1. Agregar campos de teléfono a la tabla public.tenants (si existe)
ALTER TABLE IF EXISTS public.tenants
ADD COLUMN IF NOT EXISTS phone VARCHAR(20),
ADD COLUMN IF NOT EXISTS admin_phone VARCHAR(20),
ADD COLUMN IF NOT EXISTS phone_verified BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS phone_verified_at TIMESTAMPTZ;

-- 2. Agregar índice para consultas rápidas de números de teléfono
CREATE INDEX IF NOT EXISTS idx_tenants_phone ON public.tenants(phone) WHERE phone IS NOT NULL;

-- 3. Actualizar tabla alerts_subscriptions para incluir phone
ALTER TABLE IF EXISTS public.alerts_subscriptions
ADD COLUMN IF NOT EXISTS phone VARCHAR(20),
ADD COLUMN IF NOT EXISTS notification_channel VARCHAR(50) DEFAULT 'email',
ADD COLUMN IF NOT EXISTS whatsapp_enabled BOOLEAN DEFAULT FALSE;

-- 4. Crear tabla de configuración de notificaciones por tenant si no existe
CREATE TABLE IF NOT EXISTS public.tenant_notification_config (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    slack_webhook_url TEXT,
    pagerduty_integration_key VARCHAR(255),
    twilio_account_sid VARCHAR(255),
    notification_types JSONB DEFAULT '{"critical": true, "high": true, "medium": false, "low": false}',
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id)
);

-- 5. Crear índice para acceso rápido
CREATE INDEX IF NOT EXISTS idx_tenant_notif_tenant_id ON public.tenant_notification_config(tenant_id);

-- 6. Tabla de auditoría de alertas enviadas por WhatsApp
CREATE TABLE IF NOT EXISTS public.whatsapp_alert_log (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL,
    sensor_id VARCHAR(100),
    phone_number VARCHAR(20) NOT NULL,
    alert_type VARCHAR(50),
    severity VARCHAR(20),
    message_text TEXT,
    twilio_message_sid VARCHAR(255),
    delivery_status VARCHAR(50) DEFAULT 'pending',
    delivered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (tenant_id) REFERENCES public.tenant_notification_config(tenant_id) ON DELETE CASCADE
);

-- 7. Crear índices para auditoría
CREATE INDEX IF NOT EXISTS idx_whatsapp_log_tenant ON public.whatsapp_alert_log(tenant_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_log_status ON public.whatsapp_alert_log(delivery_status);
CREATE INDEX IF NOT EXISTS idx_whatsapp_log_created ON public.whatsapp_alert_log(created_at);

-- 8. Configuración admin del sistema (números de emergencia globales)
CREATE TABLE IF NOT EXISTS public.system_emergency_contacts (
    id BIGSERIAL PRIMARY KEY,
    contact_name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    role VARCHAR(50) NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(phone_number, role)
);

-- 9. Insertar número admin del sistema
INSERT INTO public.system_emergency_contacts (contact_name, phone_number, role, active)
VALUES 
    ('Admin del Sistema - CASTÚO', '+34693443825', 'admin', TRUE),
    ('Soporte Técnico - CASTÚO', '+34693443825', 'technical', TRUE)
ON CONFLICT (phone_number, role) DO NOTHING;

-- 10. Crear vista para obtener configuración de notificaciones por tenant
CREATE OR REPLACE VIEW public.v_tenant_notification_summary AS
SELECT 
    t.id AS tenant_id,
    t.name AS tenant_name,
    tnc.phone,
    tnc.email,
    tnc.slack_webhook_url,
    tnc.pagerduty_integration_key,
    tnc.whatsapp_enabled,
    (SELECT COUNT(*) FROM whatsapp_alert_log WHERE tenant_id = t.id AND delivery_status = 'delivered') AS whatsapp_alerts_sent,
    tnc.updated_at
FROM public.tenants t
LEFT JOIN public.tenant_notification_config tnc ON t.id = tnc.tenant_id;

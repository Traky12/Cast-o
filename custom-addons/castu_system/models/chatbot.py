# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ChatbotSession(models.Model):
    _name = "castu.chatbot.session"
    _description = "Sesión del Chatbot IA"

    name = fields.Char(string="ID de Sesión", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                seq = self.env["ir.sequence"].next_by_code(
                    "castu.chatbot.session"
                )
                vals["name"] = seq if seq else "NEW"
        return super().create(vals_list)
    user_id = fields.Many2one(
        "res.users", string="Usuario", default=lambda self: self.env.user
    )
    fecha_inicio = fields.Datetime(
        string="Fecha de Inicio", default=fields.Datetime.now
    )
    fecha_fin = fields.Datetime(string="Fecha de Fin")
    mensaje_ids = fields.One2many(
        "castu.chatbot.mensaje", "session_id", string="Mensajes"
    )


class ChatbotMensaje(models.Model):
    _name = "castu.chatbot.mensaje"
    _description = "Mensaje del Chatbot"

    session_id = fields.Many2one(
        "castu.chatbot.session", string="Sesión", required=True
    )
    tipo = fields.Selection(
        [("usuario", "Usuario"), ("bot", "Bot")],
        required=True,
        string="Tipo",
    )
    contenido = fields.Text(string="Contenido")
    fecha = fields.Datetime(string="Fecha", default=fields.Datetime.now)
    contexto = fields.Text(string="Contexto (JSON)")

    def action_responder(self):
        """Genera respuesta vía FastAPI (Mistral)."""
        self.ensure_one()
        try:
            import urllib.request
            import json
            base = self.env["ir.config_parameter"].get_param(
                "castu.fastapi.url", "http://api:8000"
            )
            data = json.dumps(
                {
                    "question": self.contenido,
                    "contexto": self.contexto or "{}",
                }
            ).encode("utf-8")
            req = urllib.request.Request(
                f"{base}/chatbot/ask",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                out = json.loads(r.read().decode())
            respuesta = out.get("respuesta", "")
            self.env["castu.chatbot.mensaje"].create(
                {
                    "session_id": self.session_id.id,
                    "tipo": "bot",
                    "contenido": respuesta,
                    "contexto": self.contexto,
                }
            )
            return respuesta
        except Exception:
            return "Error al conectar con el asistente."

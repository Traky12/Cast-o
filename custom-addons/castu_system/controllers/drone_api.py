# -*- coding: utf-8 -*-
import json
from odoo import http
from odoo.http import request


class DroneAPI(http.Controller):
    @http.route(
        "/castu/drones/<int:drone_id>/start_mission",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def start_mission(self, drone_id, mission_type, params=None, **kw):
        drone = request.env["castu.drone"].browse(drone_id)
        if not drone.exists():
            return {"error": "Drone no encontrado"}, 404
        if drone.estado != "standby":
            return {"error": "El drone no está en standby"}, 400
        mission = drone._start_mission(mission_type, params or {})
        return {"status": "success", "mission_id": mission.id}

    @http.route(
        "/castu/drones/<int:drone_id>/telemetry",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def update_telemetry(self, drone_id, lat, lon, alt, battery, **kw):
        drone = request.env["castu.drone"].browse(drone_id)
        if not drone.exists():
            return {"error": "Drone no encontrado"}, 404
        drone.update_telemetry(float(lat), float(lon), float(alt), float(battery))
        return {"status": "success"}

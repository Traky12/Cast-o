import React, { useState, useEffect, useCallback } from "react";
import {
  Box,
  Grid,
  Paper,
  Typography,
  Slider,
  Switch,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Snackbar,
  Button,
} from "@mui/material";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import axios from "axios";
import { useKeycloak } from "@react-keycloak/web";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "",
});

function ActuatorControlCard({ name, state, onChange }) {
  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">{name}</Typography>
          <Switch
            checked={state}
            onChange={(e) => onChange(e.target.checked)}
            color="primary"
          />
        </Box>
      </CardContent>
    </Card>
  );
}

function SensorCard({ sensorId, zoneId, token }) {
  const [series, setSeries] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const res = await api.get(`/api/sensors/${zoneId}/readings`, {
        params: { sensor_id: sensorId, limit: 24 },
        headers: { Authorization: `Bearer ${token}` },
      });
      const readings = res.data.readings || [];
      setSeries(readings);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [zoneId, sensorId, token]);

  useEffect(() => {
    load();
    const id = setInterval(load, 30000);
    return () => clearInterval(id);
  }, [load]);

  if (loading) return <CircularProgress size={24} />;

  const chartData = series.map((item, index) => ({
    time: new Date(item.timestamp * 1000).toLocaleTimeString(),
    value: item.value,
    unit: item.unit,
    i: index,
  }));

  const last = series[series.length - 1];

  return (
    <Card sx={{ height: "100%" }}>
      <CardContent>
        <Typography variant="h6">{sensorId}</Typography>
        <Typography variant="body2" color="text.secondary">
          Última: {last ? `${last.value} ${last.unit}` : "—"}
        </Typography>
        <ResponsiveContainer width="100%" height={150}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="value" stroke="#228B22" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export default function HidroponicControl({ zoneId }) {
  const { keycloak } = useKeycloak();
  const [zoneData, setZoneData] = useState(null);
  const [sensores, setSensores] = useState([]);
  const [actuadores, setActuadores] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState("");
  const [snackbarOk, setSnackbarOk] = useState(true);

  const [valvulaAguaState, setValvulaAguaState] = useState(false);
  const [valvulaNutrientesState, setValvulaNutrientesState] = useState(false);
  const [ventiladorState, setVentiladorState] = useState(false);
  const [luzState, setLuzState] = useState(false);
  const [duracion, setDuracion] = useState(60);

  const token = keycloak?.token;

  const fetchZone = useCallback(async () => {
    if (!token) return;
    try {
      setLoading(true);
      const res = await api.get(`/api/zones/${zoneId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setZoneData(res.data);
      setSensores(res.data.sensores || []);
      const act = res.data.actuadores || {};
      setActuadores(act);
      setValvulaAguaState(!!act.valvula_agua?.state);
      setValvulaNutrientesState(!!act.valvula_nutrientes?.state);
      setVentiladorState(!!act.ventilador?.state);
      setLuzState(!!act.luz_led?.state);
      setError(null);
    } catch (err) {
      const msg = err.response?.data?.detail || "Error cargando zona";
      setError(msg);
      setSnackbarMessage(String(msg));
      setSnackbarOk(false);
      setSnackbarOpen(true);
    } finally {
      setLoading(false);
    }
  }, [zoneId, token]);

  useEffect(() => {
    fetchZone();
  }, [fetchZone]);

  const handleActuatorControl = async (actuatorId, state) => {
    try {
      await api.post(
        "/api/actuators/control",
        {
          actuator_id: actuatorId,
          actuator_type: actuatorId,
          state,
          duration: duracion,
          zone_id: zoneId,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSnackbarMessage(`${actuatorId} ${state ? "ON" : "OFF"}`);
      setSnackbarOk(true);
      setSnackbarOpen(true);
      fetchZone();
    } catch (err) {
      const msg = err.response?.data?.detail || "Error actuador";
      setSnackbarMessage(String(msg));
      setSnackbarOk(false);
      setSnackbarOpen(true);
    }
  };

  const emergencyStop = async () => {
    try {
      await api.post(
        `/api/zones/${zoneId}/actuators/emergency_stop`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSnackbarMessage("Parada de emergencia aplicada");
      setSnackbarOk(true);
      setSnackbarOpen(true);
      fetchZone();
    } catch (err) {
      setSnackbarMessage(String(err.response?.data?.detail || err));
      setSnackbarOk(false);
      setSnackbarOpen(true);
    }
  };

  if (!token) return <CircularProgress />;
  if (loading && !zoneData) return <CircularProgress />;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Control hidropónico — {zoneData?.nombre || zoneId}
      </Typography>

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
      >
        <Alert
          severity={snackbarOk ? "success" : "error"}
          sx={{ width: "100%" }}
          onClose={() => setSnackbarOpen(false)}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ mb: 2 }}>
        <Button variant="contained" color="error" onClick={emergencyStop}>
          Parada de emergencia (actuadores OFF)
        </Button>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 2, height: "100%" }}>
            <Typography variant="h6" gutterBottom>
              Sensores
            </Typography>
            <Grid container spacing={2}>
              {sensores.map((sensor) => (
                <Grid item xs={12} sm={6} key={sensor}>
                  <SensorCard sensorId={sensor} zoneId={zoneId} token={token} />
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 2, height: "100%" }}>
            <Typography variant="h6" gutterBottom>
              Actuadores
            </Typography>
            <Typography variant="subtitle1" gutterBottom>
              Duración pulsación (s): {duracion}
            </Typography>
            <Slider
              value={duracion}
              onChange={(_, v) => setDuracion(v)}
              min={10}
              max={600}
              step={10}
              valueLabelDisplay="auto"
            />

            {actuadores.valvula_agua !== undefined && (
              <ActuatorControlCard
                name="Válvula de agua"
                state={valvulaAguaState}
                onChange={(s) => {
                  setValvulaAguaState(s);
                  handleActuatorControl("valvula_agua", s);
                }}
              />
            )}
            {actuadores.valvula_nutrientes !== undefined && (
              <ActuatorControlCard
                name="Válvula nutrientes"
                state={valvulaNutrientesState}
                onChange={(s) => {
                  setValvulaNutrientesState(s);
                  handleActuatorControl("valvula_nutrientes", s);
                }}
              />
            )}
            {actuadores.ventilador !== undefined && (
              <ActuatorControlCard
                name="Ventilador"
                state={ventiladorState}
                onChange={(s) => {
                  setVentiladorState(s);
                  handleActuatorControl("ventilador", s);
                }}
              />
            )}
            {actuadores.luz_led !== undefined && (
              <ActuatorControlCard
                name="Luz LED"
                state={luzState}
                onChange={(s) => {
                  setLuzState(s);
                  handleActuatorControl("luz_led", s);
                }}
              />
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

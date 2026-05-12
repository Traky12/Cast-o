import React, { useState, useEffect, useCallback } from "react";
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

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "",
});

export default function SensorHistoryChart({
  zoneId,
  sensorId,
  parameter,
  days = 7,
  token,
}) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  const limit = Math.min(days * 24 * 6, 2000);

  const load = useCallback(async () => {
    if (!token || !sensorId) return;
    try {
      const res = await api.get(`/api/sensors/${zoneId}/readings`, {
        params: { sensor_id: sensorId, limit },
        headers: { Authorization: `Bearer ${token}` },
      });
      setData(res.data.readings || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [zoneId, sensorId, limit, token]);

  useEffect(() => {
    load();
  }, [load, parameter]);

  if (loading) return <div>Cargando…</div>;

  const chartData = data.map((item) => ({
    time: new Date(item.timestamp * 1000).toLocaleString(),
    value: item.value,
    unit: item.unit,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="time" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line
          type="monotone"
          dataKey="value"
          stroke="#00BFFF"
          name={parameter || sensorId}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

import React, { useState } from "react";
import { Box, Typography, Slider, TextField, Button, Paper } from "@mui/material";
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "",
});

export default function ParameterControl({
  zoneId,
  parameter,
  currentValue,
  min,
  max,
  unit,
  token,
}) {
  const [value, setValue] = useState(currentValue);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    try {
      setLoading(true);
      await api.post(
        `/api/zones/${zoneId}/parameters`,
        { parameter, value },
        { headers: { Authorization: `Bearer ${token}` } }
      );
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        {parameter.replace(/_/g, " ")}
      </Typography>
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, flexWrap: "wrap" }}>
        <Slider
          value={value}
          onChange={(_, v) => setValue(v)}
          min={min}
          max={max}
          step={0.1}
          valueLabelDisplay="auto"
          sx={{ flexGrow: 1, minWidth: 120 }}
        />
        <TextField
          value={value}
          onChange={(e) => setValue(parseFloat(e.target.value))}
          type="number"
          inputProps={{ min, max, step: 0.1 }}
          sx={{ width: 100 }}
        />
        <Typography>{unit}</Typography>
        <Button variant="contained" onClick={handleSubmit} disabled={loading}>
          {loading ? "Guardando…" : "Guardar"}
        </Button>
      </Box>
    </Paper>
  );
}

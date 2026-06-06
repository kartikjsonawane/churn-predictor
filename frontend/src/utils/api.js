// src/utils/api.js
// Central API helper – reads VITE_API_URL from .env (default: localhost:8000)

import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({ baseURL: BASE_URL, timeout: 15000 });

/** GET /health */
export async function getHealth() {
  const { data } = await api.get("/health");
  return data;
}

/** POST /predict – single customer */
export async function predictChurn(customer) {
  const { data } = await api.post("/predict", customer);
  return data;
}

/** POST /predict/batch – array of customers */
export async function predictBatch(customers) {
  const { data } = await api.post("/predict/batch", customers);
  return data;
}

/** GET /model-info */
export async function getModelInfo() {
  const { data } = await api.get("/model-info");
  return data;
}

/** POST /predict/csv – FormData with file */
export async function predictCSV(file) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/predict/csv", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

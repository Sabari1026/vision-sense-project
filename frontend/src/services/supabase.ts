/// <reference types="vite/client" />
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = (import.meta as any).env?.VITE_SUPABASE_URL || 'https://demo-vision-sense.supabase.co';
const supabaseAnonKey = (import.meta as any).env?.VITE_SUPABASE_ANON_KEY || 'demo-anon-key-placeholder';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

const rawApiUrl = (import.meta as any).env?.VITE_API_BASE_URL;
export const API_BASE_URL = rawApiUrl
  ? (rawApiUrl.startsWith('http') ? rawApiUrl : (rawApiUrl.startsWith('/') ? rawApiUrl : `https://${rawApiUrl}`))
  : 'https://visionsense-backend-9833.onrender.com/api';

export async function fetchCameras() {
  const res = await fetch(`${API_BASE_URL}/cameras`);
  return res.json();
}

export async function startCamera(cameraId: string) {
  const res = await fetch(`${API_BASE_URL}/cameras/${cameraId}/start`, { method: 'POST' });
  return res.json();
}

export async function stopCamera(cameraId: string) {
  const res = await fetch(`${API_BASE_URL}/cameras/${cameraId}/stop`, { method: 'POST' });
  return res.json();
}

export async function fetchAnalyticsOverview() {
  const res = await fetch(`${API_BASE_URL}/analytics/overview`);
  return res.json();
}

export async function fetchHourlyAnalytics() {
  const res = await fetch(`${API_BASE_URL}/analytics/hourly`);
  return res.json();
}

export async function fetchDailyAnalytics() {
  const res = await fetch(`${API_BASE_URL}/analytics/daily`);
  return res.json();
}

export async function fetchDwellAnalytics() {
  const res = await fetch(`${API_BASE_URL}/analytics/dwell`);
  return res.json();
}

export async function fetchAgeAnalytics() {
  const res = await fetch(`${API_BASE_URL}/analytics/age`);
  return res.json();
}

export async function fetchZoneAnalytics() {
  const res = await fetch(`${API_BASE_URL}/analytics/zones`);
  return res.json();
}

export async function fetchBusinessInsights() {
  const res = await fetch(`${API_BASE_URL}/analytics/insights`);
  return res.json();
}

export async function fetchVisitorSessions() {
  const res = await fetch(`${API_BASE_URL}/analytics/visitors`);
  return res.json();
}

export async function fetchSystemHealth() {
  const res = await fetch(`${API_BASE_URL}/system/health`);
  return res.json();
}

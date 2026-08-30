/// <reference types="vite/client" />
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = (import.meta as any).env?.VITE_SUPABASE_URL || 'https://demo-vision-sense.supabase.co';
const supabaseAnonKey = (import.meta as any).env?.VITE_SUPABASE_ANON_KEY || 'demo-anon-key-placeholder';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

const rawApiUrl = (import.meta as any).env?.VITE_API_BASE_URL;
export const API_BASE_URL = rawApiUrl
  ? (rawApiUrl.startsWith('http') ? rawApiUrl : (rawApiUrl.startsWith('/') ? rawApiUrl : `https://${rawApiUrl}`))
  : '/api';

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

export async function addCamera(payload: { name: string; source: string; location?: string }) {
  const res = await fetch(`${API_BASE_URL}/cameras`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return res.json();
}

export async function updateCamera(cameraId: string, payload: { name?: string; source?: string; location?: string }) {
  const res = await fetch(`${API_BASE_URL}/cameras/${cameraId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return res.json();
}

export async function fetchLiveTracks() {
  const res = await fetch(`${API_BASE_URL}/tracking/live`);
  return res.json();
}

export async function fetchEvents(limit: number = 50, cameraId?: string) {
  const url = cameraId ? `${API_BASE_URL}/events?limit=${limit}&camera_id=${cameraId}` : `${API_BASE_URL}/events?limit=${limit}`;
  const res = await fetch(url);
  return res.json();
}

export async function fetchZones(cameraId?: string) {
  const url = cameraId ? `${API_BASE_URL}/zones?camera_id=${cameraId}` : `${API_BASE_URL}/zones`;
  const res = await fetch(url);
  return res.json();
}

export async function createZone(payload: { id?: string; camera_id: string; name: string; polygon: number[][]; zone_type?: string }) {
  const res = await fetch(`${API_BASE_URL}/zones`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return res.json();
}

export async function updateZone(zoneId: string, payload: { name?: string; polygon?: number[][]; camera_id?: string }) {
  const res = await fetch(`${API_BASE_URL}/zones/${zoneId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return res.json();
}

export async function deleteZone(zoneId: string) {
  const res = await fetch(`${API_BASE_URL}/zones/${zoneId}`, { method: 'DELETE' });
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

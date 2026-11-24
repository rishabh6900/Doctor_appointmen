import type { Doctor, Appointment, AvailabilitySlot, DashboardStats } from '../types';

const API_BASE = '/api/v1';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!res.ok) {
    let errorDetail = 'API request failed';
    try {
      const errorJson = await res.json();
      errorDetail = errorJson.detail || errorJson.message || JSON.stringify(errorJson);
    } catch {
      errorDetail = `Status code ${res.status}: ${res.statusText}`;
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  async getHealth(): Promise<{ status: string; environment: string }> {
    return fetchJson('/health');
  },

  async getSpecialities(): Promise<string[]> {
    return fetchJson(`${API_BASE}/specialities`);
  },

  async getDoctors(speciality?: string): Promise<Doctor[]> {
    const q = speciality ? `?speciality=${encodeURIComponent(speciality)}` : '';
    return fetchJson(`${API_BASE}/doctors${q}`);
  },

  async getDoctor(id: number): Promise<Doctor> {
    return fetchJson(`${API_BASE}/doctors/${id}`);
  },

  async getAvailableSlots(date?: string, doctorId?: number, speciality?: string): Promise<AvailabilitySlot[]> {
    const params = new URLSearchParams();
    if (date) params.append('target_date', date);
    if (doctorId) params.append('doctor_id', doctorId.toString());
    if (speciality) params.append('speciality', speciality);
    return fetchJson(`${API_BASE}/availability?${params.toString()}`);
  },

  async getAppointments(status?: string, date?: string): Promise<Appointment[]> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (date) params.append('date', date);
    return fetchJson(`${API_BASE}/appointments?${params.toString()}`);
  },

  async cancelAppointment(appointmentId: number, patientPhone: string, reason?: string): Promise<Appointment> {
    return fetchJson(`${API_BASE}/appointments/${appointmentId}/cancel`, {
      method: 'POST',
      body: JSON.stringify({
        patient_phone: patientPhone,
        reason: reason || 'Cancelled via clinical dashboard',
        action_confirmed: true,
      }),
    });
  },

  async getDashboardStats(): Promise<DashboardStats> {
    return fetchJson(`${API_BASE}/dashboard/stats`);
  },

  async sendVoiceOffer(sdp: string, type: string = 'offer'): Promise<{ sdp: string; type: string; session_id: string }> {
    return fetchJson(`${API_BASE}/voice/offer`, {
      method: 'POST',
      body: JSON.stringify({ sdp, type }),
    });
  },

  async endVoiceSession(sessionId: string): Promise<{ success: boolean; session_id: string }> {
    return fetchJson(`${API_BASE}/voice/sessions/${sessionId}/end`, {
      method: 'POST',
    });
  },
};

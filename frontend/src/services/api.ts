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
    const res = await fetchJson<{ total: number; items: Doctor[] } | Doctor[]>(`${API_BASE}/doctors${q}`);
    if (Array.isArray(res)) return res;
    return res.items || [];
  },

  async getDoctor(id: number): Promise<Doctor> {
    return fetchJson(`${API_BASE}/doctors/${id}`);
  },

  async getAvailableSlots(date?: string, doctorId?: number, speciality?: string): Promise<AvailabilitySlot[]> {
    const params = new URLSearchParams();
    if (date) params.append('target_date', date);
    if (doctorId) params.append('doctor_id', doctorId.toString());
    if (speciality) params.append('speciality', speciality);
    const res = await fetchJson<any>(`${API_BASE}/availability?${params.toString()}`);
    
    // Parse backend structure: { results: [{ doctor_id, doctor_name, speciality, schedules: [{ date, time_slots: [] }] }] }
    const flatSlots: AvailabilitySlot[] = [];
    if (res && res.results && Array.isArray(res.results)) {
      for (const doc of res.results) {
        if (doc.schedules && Array.isArray(doc.schedules)) {
          for (const sched of doc.schedules) {
            if (sched.time_slots && Array.isArray(sched.time_slots)) {
              for (const time of sched.time_slots) {
                flatSlots.push({
                  doctor_id: doc.doctor_id,
                  doctor_name: doc.doctor_name,
                  speciality: doc.speciality,
                  date: sched.date,
                  time: time,
                });
              }
            }
          }
        }
      }
    } else if (Array.isArray(res)) {
      return res;
    }
    return flatSlots;
  },

  async getAppointments(status?: string, date?: string): Promise<Appointment[]> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (date) params.append('date', date);
    const res = await fetchJson<{ total: number; items: Appointment[] } | Appointment[]>(`${API_BASE}/appointments?${params.toString()}`);
    if (Array.isArray(res)) return res;
    return res.items || [];
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

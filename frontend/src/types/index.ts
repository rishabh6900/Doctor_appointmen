export interface Doctor {
  id: number;
  name: string;
  speciality: string;
  experience_years?: number;
  description?: string | null;
  phone?: string | null;
  email?: string | null;
  consultation_fee?: number | null;
  bio?: string | null;
  is_active: boolean;
}

export interface AvailabilitySlot {
  doctor_id: number;
  doctor_name: string;
  speciality: string;
  date: string;
  time: string;
  datetime_iso?: string;
}

export interface Appointment {
  id: number;
  doctor_id: number;
  doctor_name?: string;
  speciality?: string;
  patient_name: string;
  patient_phone_number: string;
  patient_phone?: string;
  appointment_date: string;
  appointment_time: string;
  status: 'confirmed' | 'cancelled' | 'rescheduled' | 'completed';
  notes?: string | null;
  created_at?: string;
  cancelled_at?: string | null;
}

export interface DashboardStats {
  total_doctors: number;
  total_appointments: number;
  active_confirmed: number;
  cancelled: number;
  today_appointments: number;
  specialities_count: number;
}

export interface CallTranscriptMessage {
  id: string;
  sender: 'user' | 'assistant' | 'system';
  text: string;
  timestamp: string;
  is_tool_call?: boolean;
}

export type CallState = 'idle' | 'requesting_mic' | 'connecting' | 'ringing' | 'connected' | 'ended' | 'failed';

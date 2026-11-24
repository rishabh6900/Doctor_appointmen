import type { DashboardStats } from '../types';
import { Users, CalendarCheck, CalendarX, Clock, Stethoscope, PhoneCall } from 'lucide-react';

interface StatsOverviewProps {
  stats: DashboardStats | null;
  loading: boolean;
  onOpenVoiceModal: () => void;
}

export const StatsOverview = ({ stats, loading, onOpenVoiceModal }: StatsOverviewProps) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-28 bg-slate-200 rounded-2xl"></div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Hero Clinic Banner */}
      <div className="relative overflow-hidden bg-gradient-to-r from-teal-700 via-teal-800 to-navy-900 rounded-3xl p-6 sm:p-8 text-white shadow-lg">
        <div className="relative z-10 max-w-2xl space-y-3">
          <div className="inline-flex items-center gap-2 bg-teal-500/20 text-teal-200 border border-teal-400/30 text-xs px-3 py-1 rounded-full font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            AI Voice Booking Receptionist Active
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            CarePoint Health Appointment Reception
          </h1>
          <p className="text-teal-100 text-sm sm:text-base leading-relaxed">
            Patients can book, reschedule, or cancel consultations via real-time conversational voice. Powered by Pipecat 1.x, Google Gemini Flash, ElevenLabs STT/TTS, and Silero VAD.
          </p>
          <div className="pt-2 flex flex-wrap gap-3">
            <button
              onClick={onOpenVoiceModal}
              className="inline-flex items-center gap-2 bg-white text-teal-800 hover:bg-teal-50 px-5 py-2.5 rounded-xl font-semibold text-sm shadow-md transition-colors"
            >
              <PhoneCall className="w-4 h-4 text-teal-600" />
              Try Spoken Voice Booking
            </button>
            <div className="text-xs text-teal-200 flex items-center gap-2 px-3 py-2 rounded-xl bg-white/10 backdrop-blur-sm">
              <span>Operating Hours: 09:00 - 17:00 IST</span>
            </div>
          </div>
        </div>
        {/* Background decorative watermark */}
        <div className="absolute -right-8 -bottom-8 opacity-10 pointer-events-none">
          <Stethoscope className="w-64 h-64 text-white" />
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Doctors</p>
            <p className="text-2xl font-bold text-slate-900 mt-1">{stats?.total_doctors ?? 0}</p>
            <p className="text-xs text-teal-600 font-medium mt-1">Across {stats?.specialities_count ?? 0} specialties</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center">
            <Users className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Confirmed Bookings</p>
            <p className="text-2xl font-bold text-emerald-600 mt-1">{stats?.active_confirmed ?? 0}</p>
            <p className="text-xs text-slate-500 font-medium mt-1">Total {stats?.total_appointments ?? 0} booked</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <CalendarCheck className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Cancelled</p>
            <p className="text-2xl font-bold text-rose-600 mt-1">{stats?.cancelled ?? 0}</p>
            <p className="text-xs text-slate-500 font-medium mt-1">Slots released automatically</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center">
            <CalendarX className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Today's Schedule</p>
            <p className="text-2xl font-bold text-blue-600 mt-1">{stats?.today_appointments ?? 0}</p>
            <p className="text-xs text-slate-500 font-medium mt-1">Scheduled for today</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <Clock className="w-6 h-6" />
          </div>
        </div>
      </div>
    </div>
  );
};

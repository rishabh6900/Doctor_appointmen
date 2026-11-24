import { useState } from 'react';
import type { Appointment } from '../types';
import { Calendar, Clock, Phone, CheckCircle, XCircle, ShieldCheck } from 'lucide-react';

interface AppointmentsTableProps {
  appointments: Appointment[];
  loading: boolean;
  onCancelAppointment: (appointment: Appointment) => void;
  onRefresh: () => void;
}

export const AppointmentsTable = ({
  appointments,
  loading,
  onCancelAppointment,
  onRefresh,
}: AppointmentsTableProps) => {
  const [statusFilter, setStatusFilter] = useState<'all' | 'confirmed' | 'cancelled'>('all');
  const [searchPhone, setSearchPhone] = useState('');

  const filtered = appointments.filter((app) => {
    const matchesStatus = statusFilter === 'all' || app.status === statusFilter;
    const phone = app.patient_phone || app.patient_phone_number || '';
    const name = app.patient_name || '';
    const matchesPhone = !searchPhone || phone.includes(searchPhone) || name.toLowerCase().includes(searchPhone.toLowerCase());
    return matchesStatus && matchesPhone;
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-4 rounded-2xl border border-slate-200">
        <div>
          <h2 className="text-lg font-bold text-slate-900">Patient Appointments</h2>
          <p className="text-xs text-slate-500">Real-time appointments ledger booked via Spoken Voice & Dashboard</p>
        </div>

        <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
          <input
            type="text"
            placeholder="Search patient / phone..."
            value={searchPhone}
            onChange={(e) => setSearchPhone(e.target.value)}
            className="text-xs px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 bg-slate-50"
          />

          <div className="inline-flex rounded-xl bg-slate-100 p-1">
            <button
              onClick={() => setStatusFilter('all')}
              className={`text-xs px-3 py-1 rounded-lg font-medium transition-all ${
                statusFilter === 'all' ? 'bg-white shadow-sm text-slate-900' : 'text-slate-600'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setStatusFilter('confirmed')}
              className={`text-xs px-3 py-1 rounded-lg font-medium transition-all ${
                statusFilter === 'confirmed' ? 'bg-white shadow-sm text-emerald-700' : 'text-slate-600'
              }`}
            >
              Confirmed
            </button>
            <button
              onClick={() => setStatusFilter('cancelled')}
              className={`text-xs px-3 py-1 rounded-lg font-medium transition-all ${
                statusFilter === 'cancelled' ? 'bg-white shadow-sm text-rose-700' : 'text-slate-600'
              }`}
            >
              Cancelled
            </button>
          </div>

          <button
            onClick={onRefresh}
            className="text-xs px-3 py-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-600 font-medium"
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold">
              <tr>
                <th className="px-5 py-3.5">ID</th>
                <th className="px-5 py-3.5">Patient Info</th>
                <th className="px-5 py-3.5">Physician & Specialty</th>
                <th className="px-5 py-3.5">Date & Time</th>
                <th className="px-5 py-3.5">Status</th>
                <th className="px-5 py-3.5">Security / Notes</th>
                <th className="px-5 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-5 py-12 text-center text-slate-400">
                    Loading appointments records...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-5 py-12 text-center text-slate-500">
                    No appointment records match the selected filters.
                  </td>
                </tr>
              ) : (
                filtered.map((app) => (
                  <tr key={app.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-5 py-4 font-mono font-bold text-slate-700">#{app.id}</td>
                    <td className="px-5 py-4">
                      <div className="font-semibold text-slate-900">{app.patient_name}</div>
                      <div className="flex items-center gap-1 text-slate-500 text-[11px] font-mono mt-0.5">
                        <Phone className="w-3 h-3 text-slate-400" />
                        <span>{app.patient_phone || app.patient_phone_number}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      <div className="font-medium text-slate-900">{app.doctor_name || `Doctor #${app.doctor_id}`}</div>
                      <div className="text-[11px] text-teal-700 font-medium">{app.speciality || 'General'}</div>
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-1.5 font-medium text-slate-900">
                        <Calendar className="w-3.5 h-3.5 text-teal-600" />
                        <span>{app.appointment_date}</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-slate-500 text-[11px] mt-0.5">
                        <Clock className="w-3 h-3 text-slate-400" />
                        <span>{app.appointment_time}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      {app.status === 'confirmed' ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <CheckCircle className="w-3 h-3" />
                          Confirmed
                        </span>
                      ) : app.status === 'cancelled' ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                          <XCircle className="w-3 h-3" />
                          Cancelled
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-700">
                          {app.status}
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-4 max-w-xs">
                      <div className="flex items-center gap-1 text-slate-500 text-[11px]">
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                        <span className="truncate">{app.notes || 'Spoken Voice Booking Verified'}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4 text-right">
                      {app.status === 'confirmed' ? (
                        <button
                          onClick={() => onCancelAppointment(app)}
                          className="text-xs font-semibold px-2.5 py-1 text-rose-700 hover:text-white bg-rose-50 hover:bg-rose-600 rounded-lg transition-colors border border-rose-200 hover:border-transparent"
                        >
                          Cancel
                        </button>
                      ) : (
                        <span className="text-[11px] text-slate-400">Archived</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

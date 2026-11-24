import type { AvailabilitySlot, Doctor } from '../types';
import { Clock } from 'lucide-react';

interface AvailabilityViewerProps {
  slots: AvailabilitySlot[];
  doctors: Doctor[];
  specialities: string[];
  selectedDate: string;
  onDateChange: (date: string) => void;
  selectedDoctorId?: number;
  onDoctorChange: (id?: number) => void;
  loading: boolean;
  onOpenVoiceModal: () => void;
}

export const AvailabilityViewer = ({
  slots,
  doctors,
  selectedDate,
  onDateChange,
  selectedDoctorId,
  onDoctorChange,
  loading,
  onOpenVoiceModal,
}: AvailabilityViewerProps) => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-4 rounded-2xl border border-slate-200">
        <div>
          <h2 className="text-lg font-bold text-slate-900">Live Doctor Slot Availability</h2>
          <p className="text-xs text-slate-500">
            Real-time computed 30-minute booking windows available for voice and clinic reservation
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 uppercase">Target Date</label>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => onDateChange(e.target.value)}
              className="text-xs px-3 py-1.5 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 bg-slate-50 font-medium"
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-500 uppercase">Doctor</label>
            <select
              value={selectedDoctorId || ''}
              onChange={(e) => onDoctorChange(e.target.value ? Number(e.target.value) : undefined)}
              className="text-xs px-3 py-1.5 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 bg-slate-50 font-medium"
            >
              <option value="">All Physicians</option>
              {doctors.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.speciality})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-16 bg-white rounded-2xl border border-slate-200 text-slate-400 animate-pulse">
          Computing available clinic slots...
        </div>
      ) : slots.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl border border-dashed border-slate-300 space-y-3">
          <p className="text-slate-600 font-medium">No available slots found for the selected date and filters.</p>
          <p className="text-xs text-slate-400">Doctors may be off-duty or all 30-minute consultation slots have been filled.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {slots.map((slot, idx) => (
            <div
              key={`${slot.doctor_id}-${slot.date}-${slot.time}-${idx}`}
              className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm hover:border-teal-400 hover:shadow transition-all flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold text-teal-800 bg-teal-50 px-2 py-0.5 rounded-md">
                    {slot.speciality}
                  </span>
                  <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                </div>
                <h4 className="font-semibold text-slate-900 text-sm">{slot.doctor_name}</h4>
                <div className="flex items-center gap-1.5 text-xs text-slate-600 pt-1">
                  <Clock className="w-3.5 h-3.5 text-teal-600" />
                  <span className="font-mono font-medium">{slot.time}</span>
                  <span className="text-slate-400">•</span>
                  <span>{slot.date}</span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[11px] text-emerald-600 font-medium">Available</span>
                <button
                  onClick={onOpenVoiceModal}
                  className="text-xs font-semibold text-teal-700 hover:text-teal-900 bg-teal-50 hover:bg-teal-100 px-2.5 py-1 rounded-lg transition-colors"
                >
                  Book via Voice
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

import { useState } from 'react';
import type { Doctor } from '../types';
import { Search, Stethoscope, Mail, Phone, DollarSign, Calendar } from 'lucide-react';

interface DoctorDirectoryProps {
  doctors: Doctor[];
  specialities: string[];
  selectedSpeciality: string;
  onSelectSpeciality: (speciality: string) => void;
  onViewSchedule: (doctor: Doctor) => void;
}

export const DoctorDirectory = ({
  doctors,
  specialities,
  selectedSpeciality,
  onSelectSpeciality,
  onViewSchedule,
}: DoctorDirectoryProps) => {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredDoctors = doctors.filter((doc) => {
    const matchesSearch =
      doc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.speciality.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSpeciality = !selectedSpeciality || doc.speciality === selectedSpeciality;
    return matchesSearch && matchesSpeciality;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Physicians & Specialists</h2>
          <p className="text-sm text-slate-500">CarePoint Health verified medical staff directory</p>
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search doctor or specialty..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent bg-white shadow-sm"
          />
        </div>
      </div>

      {/* Specialty Filter Pills */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => onSelectSpeciality('')}
          className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
            !selectedSpeciality
              ? 'bg-teal-600 text-white shadow-sm'
              : 'bg-white text-slate-600 border border-slate-200 hover:border-slate-300'
          }`}
        >
          All Specialties ({doctors.length})
        </button>
        {specialities.map((spec) => {
          const count = doctors.filter((d) => d.speciality === spec).length;
          return (
            <button
              key={spec}
              onClick={() => onSelectSpeciality(spec)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                selectedSpeciality === spec
                  ? 'bg-teal-600 text-white shadow-sm'
                  : 'bg-white text-slate-600 border border-slate-200 hover:border-slate-300'
              }`}
            >
              {spec} ({count})
            </button>
          );
        })}
      </div>

      {/* Doctor Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredDoctors.map((doctor) => (
          <div
            key={doctor.id}
            className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 flex flex-col justify-between hover:border-teal-300 hover:shadow-md transition-all group"
          >
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center font-bold text-lg group-hover:bg-teal-600 group-hover:text-white transition-colors">
                    {doctor.name.replace('Dr. ', '').charAt(0)}
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900 group-hover:text-teal-700 transition-colors">
                      {doctor.name}
                    </h3>
                    <div className="inline-flex items-center gap-1 text-xs font-medium text-teal-600 bg-teal-50 px-2 py-0.5 rounded-md mt-0.5">
                      <Stethoscope className="w-3 h-3" />
                      <span>{doctor.speciality}</span>
                    </div>
                  </div>
                </div>
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" title="Active"></span>
              </div>

              {(doctor.bio || doctor.description) && (
                <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">
                  {doctor.bio || doctor.description}
                </p>
              )}

              <div className="space-y-1.5 text-xs text-slate-500 pt-2 border-t border-slate-100">
                {doctor.email && (
                  <div className="flex items-center gap-2">
                    <Mail className="w-3.5 h-3.5 text-slate-400" />
                    <span>{doctor.email}</span>
                  </div>
                )}
                {doctor.phone && (
                  <div className="flex items-center gap-2">
                    <Phone className="w-3.5 h-3.5 text-slate-400" />
                    <span>{doctor.phone}</span>
                  </div>
                )}
                <div className="flex items-center gap-2 font-medium text-slate-700">
                  <DollarSign className="w-3.5 h-3.5 text-slate-400" />
                  <span>Consultation Fee: ₹{doctor.consultation_fee ?? 500}</span>
                </div>
              </div>
            </div>

            <div className="pt-4 mt-4 border-t border-slate-100">
              <button
                onClick={() => onViewSchedule(doctor)}
                className="w-full inline-flex items-center justify-center gap-2 text-xs font-semibold py-2 px-3 rounded-xl bg-slate-100 hover:bg-teal-50 text-slate-700 hover:text-teal-700 transition-colors"
              >
                <Calendar className="w-3.5 h-3.5" />
                View Slots & Availability
              </button>
            </div>
          </div>
        ))}
      </div>

      {filteredDoctors.length === 0 && (
        <div className="text-center py-12 bg-white rounded-2xl border border-dashed border-slate-300">
          <p className="text-slate-500 text-sm">No doctors found matching the selected criteria.</p>
        </div>
      )}
    </div>
  );
};

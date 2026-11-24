import { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { StatsOverview } from './components/StatsOverview';
import { DoctorDirectory } from './components/DoctorDirectory';
import { AppointmentsTable } from './components/AppointmentsTable';
import { AvailabilityViewer } from './components/AvailabilityViewer';
import { VoiceCallModal } from './components/VoiceCallModal';
import { api } from './services/api';
import { wsClient } from './services/websocket';
import type { Doctor, Appointment, AvailabilitySlot, DashboardStats } from './types';

export function App() {
  const [activeTab, setActiveTab] = useState<'overview' | 'doctors' | 'appointments' | 'availability'>('overview');
  const [isVoiceModalOpen, setIsVoiceModalOpen] = useState(false);

  // Data states
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [specialities, setSpecialities] = useState<string[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [availabilitySlots, setAvailabilitySlots] = useState<AvailabilitySlot[]>([]);

  // Filter states
  const [selectedSpeciality, setSelectedSpeciality] = useState<string>('');
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [selectedDoctorId, setSelectedDoctorId] = useState<number | undefined>(undefined);

  // Loading states
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingAppointments, setLoadingAppointments] = useState(true);
  const [loadingAvailability, setLoadingAvailability] = useState(false);

  const loadInitialData = async () => {
    try {
      const [statsData, specsData, docsData, appsData] = await Promise.all([
        api.getDashboardStats().catch(() => null),
        api.getSpecialities().catch(() => []),
        api.getDoctors().catch(() => []),
        api.getAppointments().catch(() => []),
      ]);

      if (statsData) setStats(statsData);
      setSpecialities(specsData);
      setDoctors(docsData);
      setAppointments(appsData);
    } finally {
      setLoadingStats(false);
      setLoadingAppointments(false);
    }
  };

  const loadAvailability = async () => {
    setLoadingAvailability(true);
    try {
      const slots = await api.getAvailableSlots(selectedDate, selectedDoctorId, selectedSpeciality || undefined);
      setAvailabilitySlots(slots);
    } catch (err) {
      console.error('Failed to load availability:', err);
      setAvailabilitySlots([]);
    } finally {
      setLoadingAvailability(false);
    }
  };

  useEffect(() => {
    loadInitialData();

    // Connect WebSocket and listen for live booking and cancellation events
    wsClient.connect();

    const unsubBooked = wsClient.on('appointment_booked', () => {
      handleRefreshAppointments();
      loadAvailability();
    });

    const unsubCancelled = wsClient.on('appointment_cancelled', () => {
      handleRefreshAppointments();
      loadAvailability();
    });

    return () => {
      unsubBooked();
      unsubCancelled();
    };
  }, []);

  useEffect(() => {
    if (activeTab === 'availability' || activeTab === 'overview') {
      loadAvailability();
    }
  }, [selectedDate, selectedDoctorId, selectedSpeciality, activeTab]);

  const handleRefreshAppointments = async () => {
    setLoadingAppointments(true);
    try {
      const [appsData, statsData] = await Promise.all([
        api.getAppointments(),
        api.getDashboardStats(),
      ]);
      setAppointments(appsData);
      setStats(statsData);
    } catch (err) {
      console.error('Refresh appointments failed:', err);
    } finally {
      setLoadingAppointments(false);
    }
  };

  const handleCancelAppointment = async (app: Appointment) => {
    if (!window.confirm(`Are you sure you want to cancel the appointment for ${app.patient_name} with ${app.doctor_name}?`)) {
      return;
    }
    const phone = app.patient_phone || app.patient_phone_number || '';
    try {
      await api.cancelAppointment(app.id, phone, 'Cancelled via clinical dashboard UI');
      await handleRefreshAppointments();
      if (activeTab === 'availability') {
        loadAvailability();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to cancel appointment';
      alert(`Cancellation failed: ${msg}`);
    }
  };

  const handleViewDoctorSchedule = (doctor: Doctor) => {
    setSelectedDoctorId(doctor.id);
    setActiveTab('availability');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenVoiceModal={() => setIsVoiceModalOpen(true)}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full space-y-8">
        {activeTab === 'overview' && (
          <div className="space-y-8">
            <StatsOverview
              stats={stats}
              loading={loadingStats}
              onOpenVoiceModal={() => setIsVoiceModalOpen(true)}
            />
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="lg:col-span-2 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-slate-900">Recent Appointments</h3>
                  <button
                    onClick={() => setActiveTab('appointments')}
                    className="text-xs text-teal-700 hover:text-teal-900 font-semibold"
                  >
                    View All →
                  </button>
                </div>
                <AppointmentsTable
                  appointments={appointments.slice(0, 5)}
                  loading={loadingAppointments}
                  onCancelAppointment={handleCancelAppointment}
                  onRefresh={handleRefreshAppointments}
                />
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-slate-900">Physicians</h3>
                  <button
                    onClick={() => setActiveTab('doctors')}
                    className="text-xs text-teal-700 hover:text-teal-900 font-semibold"
                  >
                    View All →
                  </button>
                </div>
                <div className="bg-white p-4 rounded-2xl border border-slate-200 divide-y divide-slate-100">
                  {doctors.slice(0, 5).map((doc) => (
                    <div key={doc.id} className="py-2.5 first:pt-0 last:pb-0 flex items-center justify-between">
                      <div>
                        <p className="text-xs font-semibold text-slate-900">{doc.name}</p>
                        <p className="text-[11px] text-teal-700">{doc.speciality}</p>
                      </div>
                      <button
                        onClick={() => handleViewDoctorSchedule(doc)}
                        className="text-[11px] text-slate-500 hover:text-teal-700 font-medium"
                      >
                        Slots →
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'doctors' && (
          <DoctorDirectory
            doctors={doctors}
            specialities={specialities}
            selectedSpeciality={selectedSpeciality}
            onSelectSpeciality={setSelectedSpeciality}
            onViewSchedule={handleViewDoctorSchedule}
          />
        )}

        {activeTab === 'appointments' && (
          <AppointmentsTable
            appointments={appointments}
            loading={loadingAppointments}
            onCancelAppointment={handleCancelAppointment}
            onRefresh={handleRefreshAppointments}
          />
        )}

        {activeTab === 'availability' && (
          <AvailabilityViewer
            slots={availabilitySlots}
            doctors={doctors}
            specialities={specialities}
            selectedDate={selectedDate}
            onDateChange={setSelectedDate}
            selectedDoctorId={selectedDoctorId}
            onDoctorChange={setSelectedDoctorId}
            loading={loadingAvailability}
            onOpenVoiceModal={() => setIsVoiceModalOpen(true)}
          />
        )}
      </main>

      <footer className="bg-white border-t border-slate-200 py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-xs text-slate-500 space-y-1">
          <p className="font-medium text-slate-700">CarePoint Health Medical Clinic • AI Voice Appointment Booking System</p>
          <p>Powered by Pipecat 1.x, Google Gemini Flash, ElevenLabs STT/TTS, Silero VAD, and FastAPI</p>
        </div>
      </footer>

      {/* Spoken Voice Assistant Modal */}
      <VoiceCallModal
        isOpen={isVoiceModalOpen}
        onClose={() => setIsVoiceModalOpen(false)}
        onAppointmentUpdated={handleRefreshAppointments}
      />
    </div>
  );
}

export default App;

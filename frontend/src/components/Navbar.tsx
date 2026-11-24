import { PhoneCall, Activity } from 'lucide-react';

interface NavbarProps {
  activeTab: 'overview' | 'doctors' | 'appointments' | 'availability';
  setActiveTab: (tab: 'overview' | 'doctors' | 'appointments' | 'availability') => void;
  onOpenVoiceModal: () => void;
}

export const Navbar = ({ activeTab, setActiveTab, onOpenVoiceModal }: NavbarProps) => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-teal-600 flex items-center justify-center text-white shadow-teal-100 shadow-md">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-slate-900 text-lg tracking-tight">CarePoint Health</span>
                <span className="text-xs bg-teal-100 text-teal-800 font-semibold px-2 py-0.5 rounded-full uppercase tracking-wider">AI Voice</span>
              </div>
              <p className="text-xs text-slate-500">Autonomous Doctor Appointment Management</p>
            </div>
          </div>

          <nav className="hidden md:flex space-x-1">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'overview'
                  ? 'bg-teal-50 text-teal-700'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('doctors')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'doctors'
                  ? 'bg-teal-50 text-teal-700'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              Doctors & Specialties
            </button>
            <button
              onClick={() => setActiveTab('appointments')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'appointments'
                  ? 'bg-teal-50 text-teal-700'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              Appointments
            </button>
            <button
              onClick={() => setActiveTab('availability')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'availability'
                  ? 'bg-teal-50 text-teal-700'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              Live Availability
            </button>
          </nav>

          <div className="flex items-center space-x-3">
            <button
              onClick={onOpenVoiceModal}
              className="inline-flex items-center space-x-2 bg-teal-600 hover:bg-teal-700 text-white font-medium text-sm px-4 py-2 rounded-xl shadow-sm hover:shadow transition-all group"
            >
              <PhoneCall className="w-4 h-4 group-hover:scale-110 transition-transform text-teal-100" />
              <span>Call Receptionist</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

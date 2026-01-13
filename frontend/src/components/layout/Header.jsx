import React, { useState, useRef, useEffect } from 'react';
import { Bell, Search, LogOut, User } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const Header = ({ title }) => {
    const [showDropdown, setShowDropdown] = useState(false);
    const dropdownRef = useRef(null);
    const { user, logout } = useAuth();

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setShowDropdown(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleLogout = () => {
        setShowDropdown(false);
        logout();
    };

    // Get initials from user name
    const getInitials = () => {
        if (!user?.name) return 'U';
        const names = user.name.split(' ');
        if (names.length >= 2) {
            return names[0][0] + names[1][0];
        }
        return names[0][0];
    };

    return (
        <header className="bg-[#B3C8DC] sticky top-0 z-10">
            <div className="px-4 sm:px-6 lg:px-8 py-3">
                <div className="flex items-center justify-end gap-3">
                    {/* Search Button */}
                    <button className="p-2.5 bg-[#D6DFEA] hover:bg-[#c5d0de] rounded-full transition-all">
                        <Search size={18} className="text-gray-600" />
                    </button>

                    {/* Notifications */}
                    <button className="p-2.5 bg-[#D6DFEA] hover:bg-[#c5d0de] rounded-full transition-all relative">
                        <Bell size={18} className="text-gray-600" />
                        <span className="absolute top-1 right-1 h-2.5 w-2.5 bg-pink-500 rounded-full
                                         ring-2 ring-white"></span>
                    </button>

                    {/* User Avatar with Dropdown */}
                    <div className="relative" ref={dropdownRef}>
                        <button
                            onClick={() => setShowDropdown(!showDropdown)}
                            className="h-10 w-10 rounded-full
                                     bg-gradient-to-br from-pink-500 to-rose-500
                                     flex items-center justify-center
                                     shadow-sm text-white font-semibold text-sm
                                     hover:shadow-md transition-all cursor-pointer"
                        >
                            {getInitials()}
                        </button>

                        {/* Dropdown Menu */}
                        {showDropdown && (
                            <div className="absolute right-0 mt-2 w-64 bg-white rounded-xl shadow-xl
                                          border border-gray-100 overflow-hidden z-50">
                                {/* User Info */}
                                <div className="px-4 py-3 border-b border-gray-100 bg-gradient-to-br from-purple-50 to-indigo-50">
                                    <div className="flex items-center gap-3">
                                        <div className="h-12 w-12 rounded-full
                                                      bg-gradient-to-br from-pink-500 to-rose-500
                                                      flex items-center justify-center
                                                      text-white font-semibold">
                                            {getInitials()}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-semibold text-gray-900 truncate">
                                                {user?.name || 'User'}
                                            </p>
                                            <p className="text-xs text-gray-500 truncate">
                                                {user?.email || ''}
                                            </p>
                                            {user?.company && (
                                                <p className="text-xs text-purple-600 font-medium mt-0.5">
                                                    {user.company}
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {/* Logout Button */}
                                <button
                                    onClick={handleLogout}
                                    className="w-full px-4 py-3 flex items-center gap-3
                                             text-left hover:bg-red-50 transition-colors
                                             text-red-600 font-medium"
                                >
                                    <LogOut size={18} />
                                    <span>Logout</span>
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;

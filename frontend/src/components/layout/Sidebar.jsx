import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
    LayoutDashboard,
    Package,
    Upload,
    AlertTriangle,
    BarChart3,
    MessageSquare,
    Box,
    X,
    Settings
} from 'lucide-react';

const Sidebar = ({ isOpen, onClose }) => {
    const location = useLocation();
    const [hoveredItem, setHoveredItem] = useState(null);

    const navItems = [
        { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
        { path: '/products', icon: Package, label: 'Products' },
        { path: '/upload', icon: Upload, label: 'Upload' },
        { path: '/low-confidence', icon: AlertTriangle, label: 'Low Confidence' },
        { path: '/analytics', icon: BarChart3, label: 'Analytics' },
        { path: '/chatbot', icon: MessageSquare, label: 'AI Assistant' },
    ];

    const isActivePath = (path) => {
        if (path === '/') return location.pathname === '/';
        return location.pathname.startsWith(path);
    };

    return (
        <>
            {/* Mobile Overlay */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40 lg:hidden"
                    onClick={onClose}
                />
            )}

            {/* Desktop Sidebar - Inside the box, not fixed */}
            <aside className={`
                hidden lg:flex
                w-[72px] flex-shrink-0
                bg-[#B3C8DC]
                flex-col
                custom-scrollbar overflow-y-auto
            `}>
                {/* Logo */}
                <div className="p-3 flex items-center justify-center">
                    <div className="p-2.5 bg-gradient-to-br from-pink-500 to-rose-500 rounded-xl shadow-lg">
                        <Box className="text-white" size={22} />
                    </div>
                </div>

                {/* Navigation */}
                <nav className="flex-1 p-3 space-y-2">
                    {navItems.map((item) => {
                        const isActive = isActivePath(item.path);
                        return (
                            <div
                                key={item.path}
                                className="relative"
                                onMouseEnter={() => setHoveredItem(item.path)}
                                onMouseLeave={() => setHoveredItem(null)}
                            >
                                <NavLink
                                    to={item.path}
                                    className={`
                                        flex items-center justify-center p-3
                                        rounded-xl transition-all duration-200
                                        ${isActive
                                            ? 'bg-gradient-to-r from-pink-500 to-rose-500 text-white shadow-lg'
                                            : 'text-gray-700 hover:bg-[#a3b8cc] hover:text-gray-900'
                                        }
                                    `}
                                >
                                    <item.icon size={22} />
                                </NavLink>

                                {/* Tooltip */}
                                {hoveredItem === item.path && (
                                    <div className="absolute left-full ml-3 top-1/2 -translate-y-1/2
                                                    px-3 py-2 bg-gray-900 text-white text-sm font-medium
                                                    rounded-lg shadow-lg whitespace-nowrap z-[60]
                                                    flex items-center">
                                        {item.label}
                                        <div className="absolute right-full top-1/2 -translate-y-1/2
                                                        border-8 border-transparent border-r-gray-900" />
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </nav>

                {/* Settings at bottom */}
                <div className="p-3">
                    <div
                        className="relative"
                        onMouseEnter={() => setHoveredItem('settings')}
                        onMouseLeave={() => setHoveredItem(null)}
                    >
                        <button className="w-full flex items-center justify-center p-3
                                          rounded-xl text-gray-700 hover:bg-[#a3b8cc] hover:text-gray-900
                                          transition-all duration-200">
                            <Settings size={22} />
                        </button>

                        {hoveredItem === 'settings' && (
                            <div className="absolute left-full ml-3 top-1/2 -translate-y-1/2
                                            px-3 py-2 bg-gray-900 text-white text-sm font-medium
                                            rounded-lg shadow-lg whitespace-nowrap z-[60]
                                            flex items-center">
                                Settings
                                <div className="absolute right-full top-1/2 -translate-y-1/2
                                                border-8 border-transparent border-r-gray-900" />
                            </div>
                        )}
                    </div>
                </div>
            </aside>

            {/* Mobile Sidebar - Fixed position for drawer behavior */}
            <aside className={`
                lg:hidden fixed inset-y-0 left-0 z-50
                w-64
                bg-[#B3C8DC] shadow-xl
                transform transition-transform duration-300 ease-in-out
                ${isOpen ? 'translate-x-0' : '-translate-x-full'}
                flex flex-col
                custom-scrollbar overflow-y-auto
            `}>
                {/* Logo */}
                <div className="p-4 flex items-center">
                    <div className="p-2.5 bg-gradient-to-br from-pink-500 to-rose-500 rounded-xl shadow-lg">
                        <Box className="text-white" size={22} />
                    </div>
                    <div className="ml-3">
                        <h1 className="text-lg font-bold text-gray-900">FMCG</h1>
                        <p className="text-xs text-gray-700">Master</p>
                    </div>
                    <button
                        onClick={onClose}
                        className="ml-auto p-2 hover:bg-[#a3b8cc] rounded-lg transition-colors"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 p-3 space-y-2">
                    {navItems.map((item) => {
                        const isActive = isActivePath(item.path);
                        return (
                            <NavLink
                                key={item.path}
                                to={item.path}
                                onClick={onClose}
                                className={`
                                    flex items-center gap-3 px-4 py-3
                                    rounded-xl transition-all duration-200
                                    ${isActive
                                        ? 'bg-gradient-to-r from-pink-500 to-rose-500 text-white shadow-lg'
                                        : 'text-gray-700 hover:bg-[#a3b8cc] hover:text-gray-900'
                                    }
                                `}
                            >
                                <item.icon size={22} />
                                <span className="font-medium">{item.label}</span>
                            </NavLink>
                        );
                    })}
                </nav>

                {/* Settings at bottom */}
                <div className="p-3">
                    <button className="w-full flex items-center gap-3 px-4 py-3
                                      rounded-xl text-gray-800 hover:bg-[#a3b8cc] hover:text-gray-900
                                      transition-all duration-200">
                        <Settings size={22} />
                        <span className="font-medium">Settings</span>
                    </button>
                </div>
            </aside>
        </>
    );
};

export default Sidebar;

import React from 'react';

const Badge = ({
    children,
    variant = 'default',
    size = 'md',
    className = ''
}) => {
    const variants = {
        default: 'bg-gray-100/80 text-gray-800 backdrop-blur-sm',
        success: 'bg-emerald-100/80 text-emerald-800 backdrop-blur-sm',
        warning: 'bg-amber-100/80 text-amber-800 backdrop-blur-sm',
        error: 'bg-red-100/80 text-red-800 backdrop-blur-sm',
        info: 'bg-blue-100/80 text-blue-800 backdrop-blur-sm',
        primary: 'bg-pink-100/80 text-pink-800 backdrop-blur-sm',
        secondary: 'bg-purple-100/80 text-purple-800 backdrop-blur-sm',
        // Glass variants
        glass: 'bg-white/40 backdrop-blur-sm border border-white/30 text-gray-700',
        'glass-pink': 'bg-pink-500/20 backdrop-blur-sm border border-pink-200/50 text-pink-700',
        'glass-success': 'bg-emerald-500/20 backdrop-blur-sm border border-emerald-200/50 text-emerald-700',
        'glass-warning': 'bg-amber-500/20 backdrop-blur-sm border border-amber-200/50 text-amber-700',
        'glass-info': 'bg-blue-500/20 backdrop-blur-sm border border-blue-200/50 text-blue-700',
    };

    const sizes = {
        sm: 'px-2 py-0.5 text-xs',
        md: 'px-2.5 py-1 text-sm',
        lg: 'px-3 py-1.5 text-base',
    };

    return (
        <span
            className={`
                inline-flex items-center rounded-full font-medium
                ${variants[variant]}
                ${sizes[size]}
                ${className}
            `}
        >
            {children}
        </span>
    );
};

export default Badge;

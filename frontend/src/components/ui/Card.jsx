import React from 'react';

const Card = ({
    title,
    subtitle,
    children,
    variant = 'default',
    className = '',
    onClick,
    hoverable = false
}) => {
    const variants = {
        default: 'bg-white/95 backdrop-blur-xl border-white/80',
        solid: 'bg-white border-gray-100',
        gradient: 'bg-gradient-to-br from-pink-500 to-rose-500 text-white border-0 shadow-lg',
        glass: 'bg-white/95 backdrop-blur-xl border-white/80',
        'glass-strong': 'bg-white border-white/90',
        success: 'bg-emerald-50/90 backdrop-blur-sm border-emerald-200/50',
        warning: 'bg-amber-50/90 backdrop-blur-sm border-amber-200/50',
        error: 'bg-red-50/90 backdrop-blur-sm border-red-200/50',
        info: 'bg-blue-50/90 backdrop-blur-sm border-blue-200/50',
    };

    const hoverClass = hoverable || onClick
        ? 'cursor-pointer hover:shadow-lg hover:-translate-y-1 hover:bg-white'
        : '';

    return (
        <div
            className={`
                rounded-2xl shadow-card border transition-all duration-300 p-6
                ${variants[variant]}
                ${hoverClass}
                ${className}
            `}
            onClick={onClick}
        >
            {(title || subtitle) && (
                <div className="mb-4">
                    {title && (
                        <h3 className={`text-lg font-semibold ${variant === 'gradient' ? 'text-white' : 'text-gray-900'}`}>
                            {title}
                        </h3>
                    )}
                    {subtitle && (
                        <p className={`text-sm mt-1 ${variant === 'gradient' ? 'text-white/80' : 'text-gray-500'}`}>
                            {subtitle}
                        </p>
                    )}
                </div>
            )}
            {children}
        </div>
    );
};

export default Card;

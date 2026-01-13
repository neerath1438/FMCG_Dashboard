import React from 'react';

const Button = ({
    children,
    variant = 'primary',
    size = 'md',
    icon: Icon,
    iconPosition = 'left',
    loading = false,
    disabled = false,
    className = '',
    onClick,
    type = 'button',
    ...props
}) => {
    const variants = {
        // Primary is now pink/coral gradient
        primary: 'bg-gradient-to-r from-pink-500 to-rose-500 hover:from-pink-600 hover:to-rose-600 text-white shadow-lg hover:shadow-xl',
        secondary: 'bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 text-white shadow-lg hover:shadow-xl',
        // Glass outline button
        outline: 'border-2 border-pink-500/50 text-pink-600 hover:bg-pink-50/50 backdrop-blur-sm',
        // Glass ghost button
        ghost: 'text-gray-700 hover:bg-white/60 backdrop-blur-sm',
        danger: 'bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white shadow-lg',
        success: 'bg-gradient-to-r from-emerald-500 to-green-500 hover:from-emerald-600 hover:to-green-600 text-white shadow-lg',
        // Glass variant
        glass: 'glass text-gray-700 hover:bg-white/80 border border-white/30',
        // Info variant
        info: 'bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white shadow-lg',
    };

    const sizes = {
        sm: 'px-3 py-1.5 text-sm',
        md: 'px-4 py-2.5 text-base',
        lg: 'px-6 py-3 text-lg',
    };

    const isDisabled = disabled || loading;

    return (
        <button
            type={type}
            className={`
                inline-flex items-center justify-center gap-2 rounded-xl font-medium
                transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-pink-500/40 focus:ring-offset-2
                disabled:opacity-50 disabled:cursor-not-allowed
                ${variants[variant]}
                ${sizes[size]}
                ${className}
            `}
            disabled={isDisabled}
            onClick={onClick}
            {...props}
        >
            {loading && (
                <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
            )}
            {!loading && Icon && iconPosition === 'left' && <Icon size={18} />}
            {children}
            {!loading && Icon && iconPosition === 'right' && <Icon size={18} />}
        </button>
    );
};

export default Button;

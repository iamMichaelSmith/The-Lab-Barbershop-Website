/** @type {import('tailwindcss').Config} */
module.exports = {
    content: ["./src/**/*.{njk,md,html,js}"],
    theme: {
        extend: {
            colors: {
                'lab-blue': '#0047AB',
                'lab-red': '#E0115F',
                'lab-white': '#F8F9FA',
                'lab-black': '#0A0A0A',
            },
            fontFamily: {
                outfit: ['Outfit', 'sans-serif'],
            },
            animation: {
                'pulse-slow': 'pulse-slow 8s infinite ease-in-out',
                'fade-in': 'fadeIn 1s cubic-bezier(0.23, 1, 0.32, 1) forwards',
            },
            keyframes: {
                'pulse-slow': {
                    '0%, 100%': { opacity: '0.15', transform: 'scale(1)' },
                    '50%': { opacity: '0.25', transform: 'scale(1.05)' },
                },
                fadeIn: {
                    from: { opacity: '0', transform: 'translateY(30px)' },
                    to: { opacity: '1', transform: 'translateY(0)' },
                },
            },
        },
    },
    plugins: [],
};

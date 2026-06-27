import React from 'react';

const TypingIndicator: React.FC = () => {
  return (
    <div className="flex items-center space-x-1">
      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce-dot"></div>
      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce-dot animation-delay-200"></div>
      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce-dot animation-delay-400"></div>
    </div>
  );
};

export default TypingIndicator;

// Tailwind CSS keyframes and custom animation classes
const style = document.createElement('style');
style.innerHTML = `
  @keyframes bounce-dot {
    0%, 80%, 100% {
      transform: scale(0);
    }
    40% {
      transform: scale(1);
    }
  }
  .animate-bounce-dot {
    animation: bounce-dot 1.4s infinite;
  }
  .animation-delay-200 {
    animation-delay: 0.2s;
  }
  .animation-delay-400 {
    animation-delay: 0.4s;
  }
`;
document.head.appendChild(style);
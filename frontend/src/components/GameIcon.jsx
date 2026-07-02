import React from 'react';

const GameIcon = ({ name, size = 18, style = {}, className = "" }) => {
  return (
    <img 
      src={`/icons/${name}.png`} 
      alt={name}
      className={`game-icon ${className}`}
      style={{
        width: `${size}px`,
        height: `${size}px`,
        display: 'inline-block',
        verticalAlign: 'text-bottom',
        ...style
      }}
      onError={(e) => {
        e.target.style.display = 'none';
      }}
    />
  );
};

export default GameIcon;

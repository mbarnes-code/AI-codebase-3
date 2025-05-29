import React from 'react';
import ManaSymbol from '../ManaSymbol/ManaSymbol';
import { IdentityEnum } from '@space-cow-media/spellbook-client';

type Props = {
  identity: IdentityEnum;
  size?: 'medium' | 'small';
};

const ColorIdentity: React.FC<Props> = ({ identity, size = 'medium' }) => {
  const colors = identity.toString().toUpperCase().split('');
  const colorIdentityDescription = colors.join(', ');

  return (
    <div className="w-full text-center">
      <p className="sr-only">Color Identity: {colorIdentityDescription}</p>
      {colors.map((color) => (
        <ManaSymbol symbol={color} size={size} key={color} ariaHidden />
      ))}
    </div>
  );
};

export default ColorIdentity;

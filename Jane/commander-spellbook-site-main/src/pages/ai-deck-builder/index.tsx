// src/pages/ai-deck-builder/index.tsx

import React from 'react';
import Head from 'next/head';
import AIDeckBuilder from '../../components/AIDeckBuilder/AIDeckBuilder';

const AIDeckBuilderPage: React.FC = () => {
  return (
    <>
      <Head>
        <title>AI Deck Builder - Commander Spellbook</title>
        <meta
          name="description"
          content="Generate optimized Commander decks with AI analysis. Get 100-card decklists with synergy analysis and combo detection."
        />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 py-8">
        <div className="container mx-auto px-4">
          <AIDeckBuilder />
        </div>
      </div>
    </>
  );
};

export default AIDeckBuilderPage;

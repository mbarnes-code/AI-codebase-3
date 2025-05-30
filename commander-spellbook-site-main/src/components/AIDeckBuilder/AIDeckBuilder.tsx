// src/components/AIDeckBuilder/AIDeckBuilder.tsx

import React, { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faMagic, faSpinner, faDownload, faCopy } from '@fortawesome/free-solid-svg-icons';

interface DeckSlot {
  name: string;
  target_count: number;
  cards: Array<{
    name: string;
    type_line: string;
    mana_value: number;
    oracle_text: string;
    price_tcgplayer: number;
  }>;
  priority: number;
}

interface Analysis {
  strategy: string;
  synergies: string[];
  power_level: string;
  estimated_cost: string;
  deck_slots: DeckSlot[];
  mana_curve: Record<string, number>;
  color_distribution: Record<string, number>;
}

interface DeckResponse {
  commander: string;
  format: string;
  recommended_cards: string[];
  analysis: Analysis;
  phase: string;
  status: string;
}

const AIDeckBuilder: React.FC = () => {
  const [commander, setCommander] = useState('');
  const [strategy, setStrategy] = useState('balanced');
  const [budget, setBudget] = useState('casual');
  const [loading, setLoading] = useState(false);
  const [deckData, setDeckData] = useState<DeckResponse | null>(null);
  const [error, setError] = useState('');

  const buildDeck = async () => {
    if (!commander.trim()) {
      setError('Please enter a commander name');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const response = await fetch('/api/ai/build-deck', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          commander: commander.trim(),
          format: 'commander',
          strategy_focus: strategy,
          budget_range: budget
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to build deck');
      }

      const data: DeckResponse = await response.json();
      setDeckData(data);
    } catch (err) {
      setError('Error building deck. Please try again.');
      console.error('Deck building error:', err);
    } finally {
      setLoading(false);
    }
  };

  const exportDecklist = () => {
    if (!deckData) return;

    let decklist = `// AI Generated Deck for ${deckData.commander}\n`;
    decklist += `// Strategy: ${deckData.analysis.strategy}\n`;
    decklist += `// Power Level: ${deckData.analysis.power_level}\n`;
    decklist += `// Estimated Cost: ${deckData.analysis.estimated_cost}\n\n`;
    
    decklist += `// Commander\n1x ${deckData.commander}\n\n`;
    
    deckData.analysis.deck_slots.forEach(slot => {
      if (slot.cards.length > 0) {
        decklist += `// ${slot.name.charAt(0).toUpperCase() + slot.name.slice(1)} (${slot.cards.length})\n`;
        slot.cards.forEach(card => {
          decklist += `1x ${card.name}\n`;
        });
        decklist += '\n';
      }
    });

    const blob = new Blob([decklist], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${deckData.commander.replace(/[^a-zA-Z0-9]/g, '_')}_AI_Deck.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const copyDecklist = async () => {
    if (!deckData) return;

    let decklist = `${deckData.commander}\n\n`;
    deckData.analysis.deck_slots.forEach(slot => {
      slot.cards.forEach(card => {
        decklist += `1x ${card.name}\n`;
      });
    });

    try {
      await navigator.clipboard.writeText(decklist);
      alert('Decklist copied to clipboard!');
    } catch (err) {
      console.error('Failed to copy decklist:', err);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white dark:bg-gray-800 rounded-lg shadow-lg">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          <FontAwesomeIcon icon={faMagic} className="mr-2 text-primary" />
          AI Deck Builder
        </h1>
        <p className="text-gray-600 dark:text-gray-300">
          Generate optimized 100-card Commander decks with AI analysis
        </p>
      </div>

      {/* Input Form */}
      <div className="bg-gray-50 dark:bg-gray-700 p-6 rounded-lg mb-6">
        <div className="grid md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Commander
            </label>
            <input
              type="text"
              value={commander}
              onChange={(e) => setCommander(e.target.value)}
              placeholder="e.g., Atraxa, Praetors' Voice"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary dark:bg-gray-800 dark:text-white"
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Strategy
            </label>
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary dark:bg-gray-800 dark:text-white"
              disabled={loading}
            >
              <option value="balanced">Balanced</option>
              <option value="aggro">Aggressive</option>
              <option value="control">Control</option>
              <option value="combo">Combo</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Budget
            </label>
            <select
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary dark:bg-gray-800 dark:text-white"
              disabled={loading}
            >
              <option value="budget">Budget ($50-100)</option>
              <option value="casual">Casual ($150-300)</option>
              <option value="focused">Focused ($300-600)</option>
              <option value="optimized">Optimized ($600+)</option>
            </select>
          </div>
        </div>

        <button
          onClick={buildDeck}
          disabled={loading}
          className="w-full bg-primary hover:bg-purple-600 disabled:bg-gray-400 text-white font-medium py-3 px-4 rounded-md transition-colors duration-200"
        >
          {loading ? (
            <>
              <FontAwesomeIcon icon={faSpinner} className="animate-spin mr-2" />
              Generating Deck...
            </>
          ) : (
            <>
              <FontAwesomeIcon icon={faMagic} className="mr-2" />
              Build Deck
            </>
          )}
        </button>

        {error && (
          <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}
      </div>

      {/* Results */}
      {deckData && (
        <div className="space-y-6">
          {/* Deck Summary */}
          <div className="bg-blue-50 dark:bg-blue-900 p-6 rounded-lg">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              Deck Analysis
            </h2>
            
            <div className="grid md:grid-cols-2 gap-4 mb-4">
              <div>
                <h3 className="font-semibold text-gray-700 dark:text-gray-300">Strategy</h3>
                <p className="text-gray-600 dark:text-gray-400">{deckData.analysis.strategy}</p>
              </div>
              <div>
                <h3 className="font-semibold text-gray-700 dark:text-gray-300">Power Level</h3>
                <p className="text-gray-600 dark:text-gray-400">{deckData.analysis.power_level}</p>
              </div>
              <div>
                <h3 className="font-semibold text-gray-700 dark:text-gray-300">Estimated Cost</h3>
                <p className="text-gray-600 dark:text-gray-400">{deckData.analysis.estimated_cost}</p>
              </div>
              <div>
                <h3 className="font-semibold text-gray-700 dark:text-gray-300">Total Cards</h3>
                <p className="text-gray-600 dark:text-gray-400">
                  {deckData.recommended_cards.length + 1} (including commander)
                </p>
              </div>
            </div>

            <div className="flex gap-2 mb-4">
              <button
                onClick={exportDecklist}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md transition-colors duration-200"
              >
                <FontAwesomeIcon icon={faDownload} className="mr-2" />
                Export
              </button>
              <button
                onClick={copyDecklist}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md transition-colors duration-200"
              >
                <FontAwesomeIcon icon={faCopy} className="mr-2" />
                Copy
              </button>
            </div>

            {deckData.analysis.synergies.length > 0 && (
              <div>
                <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">Synergies</h3>
                <ul className="list-disc list-inside text-gray-600 dark:text-gray-400">
                  {deckData.analysis.synergies.map((synergy, index) => (
                    <li key={index}>{synergy}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Deck Slots */}
          <div className="bg-gray-50 dark:bg-gray-700 p-6 rounded-lg">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              Deck Breakdown
            </h2>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {deckData.analysis.deck_slots
                .filter(slot => slot.cards.length > 0)
                .map((slot, index) => (
                <div key={index} className="bg-white dark:bg-gray-800 p-4 rounded border">
                  <h3 className="font-semibold text-gray-900 dark:text-white capitalize mb-2">
                    {slot.name} ({slot.cards.length})
                  </h3>
                  <div className="space-y-1 max-h-48 overflow-y-auto">
                    {slot.cards.slice(0, 10).map((card, cardIndex) => (
                      <div key={cardIndex} className="text-sm text-gray-600 dark:text-gray-400">
                        {card.name}
                        {card.price_tcgplayer > 0 && (
                          <span className="text-green-600 ml-2">
                            ${card.price_tcgplayer}
                          </span>
                        )}
                      </div>
                    ))}
                    {slot.cards.length > 10 && (
                      <div className="text-sm text-gray-500 italic">
                        ...and {slot.cards.length - 10} more
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIDeckBuilder;
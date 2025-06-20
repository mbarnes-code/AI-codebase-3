// src/pages/api/ai/build-deck.ts

import type { NextApiRequest, NextApiResponse } from 'next';

interface DeckBuildRequest {
  commander: string;
  format?: string;
  strategy_focus?: string;
  budget_range?: string;
}

interface DeckBuildResponse {
  commander: string;
  format: string;
  recommended_cards: string[];
  analysis: {
    strategy: string;
    synergies: string[];
    power_level: string;
    estimated_cost: string;
    deck_slots: Array<{
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
    }>;
    mana_curve: Record<string, number>;
    color_distribution: Record<string, number>;
  };
  phase: string;
  status: string;
}

// Improved rate limiting store (in production, use Redis or similar)
const rateLimitStore = new Map<string, { count: number; resetTime: number }>();
const RATE_LIMIT_PER_MINUTE = 5; // Reduced from 10 for security
const RATE_LIMIT_WINDOW = 60 * 1000; // 1 minute in milliseconds

function getRateLimitKey(req: NextApiRequest): string {
  // Use IP address for rate limiting with better extraction
  const forwarded = req.headers['x-forwarded-for'];
  const realIp = req.headers['x-real-ip'];
  const ip = (realIp as string) || 
            (forwarded ? (Array.isArray(forwarded) ? forwarded[0] : forwarded.split(',')[0]) : 
             req.socket.remoteAddress) || 'unknown';
  return `rate_limit:${ip.trim()}`;
}

// Input validation functions
function validateCommander(commander: string): boolean {
  if (!commander || typeof commander !== 'string') return false;
  if (commander.length < 2 || commander.length > 100) return false;
  // Basic sanitization - allow letters, numbers, spaces, common punctuation
  const allowedChars = /^[a-zA-Z0-9\s\-',\.]+$/;
  return allowedChars.test(commander);
}

function validateFormat(format: string): boolean {
  const allowedFormats = ['commander', 'edh', 'legacy', 'vintage', 'modern'];
  return allowedFormats.includes(format.toLowerCase());
}

function validateStrategy(strategy: string): boolean {
  const allowedStrategies = ['aggro', 'control', 'combo', 'midrange', 'balanced', 'tribal', 'voltron'];
  return allowedStrategies.includes(strategy.toLowerCase());
}

function validateBudget(budget: string): boolean {
  const allowedBudgets = ['budget', 'casual', 'competitive', 'cedh'];
  return allowedBudgets.includes(budget.toLowerCase());
}

function checkRateLimit(req: NextApiRequest): { allowed: boolean; remaining: number } {
  const key = getRateLimitKey(req);
  const now = Date.now();
  const windowStart = now - RATE_LIMIT_WINDOW;

  let rateLimitData = rateLimitStore.get(key);

  if (!rateLimitData || rateLimitData.resetTime < windowStart) {
    rateLimitData = { count: 0, resetTime: now + RATE_LIMIT_WINDOW };
    rateLimitStore.set(key, rateLimitData);
  }

  if (rateLimitData.count >= RATE_LIMIT_PER_MINUTE) {
    return { allowed: false, remaining: 0 };
  }

  rateLimitData.count++;
  return { allowed: true, remaining: RATE_LIMIT_PER_MINUTE - rateLimitData.count };
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<DeckBuildResponse | { error: string }>,
) {
  // Security headers
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');

  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Check rate limiting
  const rateLimitResult = checkRateLimit(req);
  if (!rateLimitResult.allowed) {
    return res.status(429).json({ error: 'Too many requests. Please try again later.' });
  }

  const {
    commander,
    format = 'commander',
    strategy_focus = 'balanced',
    budget_range = 'casual',
  }: DeckBuildRequest = req.body;

  // Enhanced input validation
  if (!commander || !validateCommander(commander)) {
    return res.status(400).json({ error: 'Invalid commander name' });
  }

  if (!validateFormat(format)) {
    return res.status(400).json({ error: 'Invalid format' });
  }

  if (!validateStrategy(strategy_focus)) {
    return res.status(400).json({ error: 'Invalid strategy focus' });
  }

  if (!validateBudget(budget_range)) {
    return res.status(400).json({ error: 'Invalid budget range' });
  }

  try {
    // Use the Motoko LLM server URL (separate server at 192.168.1.12)
    const llmUrl = process.env.NEXT_PUBLIC_LLM_SERVER_URL || 'http://192.168.1.12:8000';

    console.log(`Connecting to Motoko LLM server at: ${llmUrl}`);

    // Sanitized prompt composition
    const prompt = `Build a 100-card Commander deck for commander: ${commander.replace(/[<>]/g, '')}
Format: ${format}
Strategy: ${strategy_focus}
Budget: ${budget_range}

Please provide a detailed deck analysis and card recommendations.`;

    // Call Motoko LLM server's /generate endpoint with timeout and auth
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };

    // Add API key if available
    const apiKey = process.env.LLM_API_KEY;
    if (apiKey) {
      headers['Authorization'] = `Bearer ${apiKey}`;
    }

    const response = await fetch(`${llmUrl}/generate`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        prompt,
        model: 'llama2', // or another model as needed
        options: {
          temperature: 0.7,
          max_tokens: 1500
        },
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Motoko LLM error (${response.status}):`, errorText);
      return res.status(response.status).json({ error: `Motoko LLM error: ${response.statusText}` });
    }

    const llmData = await response.json();
    console.log('Successfully received response from Motoko LLM server');
    
    // Parse LLM response and format it for the frontend
    // For now, return a structured response with the LLM output
    const deckResponse: DeckBuildResponse = {
      commander,
      format,
      recommended_cards: [],
      analysis: {
        strategy: strategy_focus,
        synergies: [`AI Generated with ${strategy_focus} strategy`],
        power_level: budget_range === 'budget' ? 'Casual (6-7)' : budget_range === 'competitive' ? 'High (8-9)' : 'Medium (7-8)',
        estimated_cost: budget_range === 'budget' ? '$50-$150' : budget_range === 'competitive' ? '$500+' : '$150-$500',
        deck_slots: [
          {
            name: 'AI Generated Cards',
            target_count: 99,
            cards: [{
              name: 'Generated by Motoko LLM',
              type_line: 'AI Response',
              mana_value: 0,
              oracle_text: llmData.response || 'No response received',
              price_tcgplayer: 0,
            }],
            priority: 10,
          }
        ],
        mana_curve: { '0': 5, '1': 8, '2': 12, '3': 15, '4': 12, '5': 8, '6': 5, '7+': 3 },
        color_distribution: {},
      },
      phase: 'completed',
      status: 'success',
    };

    // Add rate limit headers
    res.setHeader('X-RateLimit-Limit', RATE_LIMIT_PER_MINUTE);
    res.setHeader('X-RateLimit-Remaining', rateLimitResult.remaining);
    res.setHeader('X-RateLimit-Reset', Math.ceil((Date.now() + RATE_LIMIT_WINDOW) / 1000));

    return res.status(200).json(deckResponse);
  } catch (error) {
    console.error('Error calling Motoko LLM server:', error);

    if (error instanceof Error && error.name === 'AbortError') {
      return res.status(408).json({
        error: 'Request to Motoko LLM server timed out after 30 seconds. Please try again.',
      });
    }

    if (error instanceof TypeError && error.message.includes('fetch')) {
      return res.status(503).json({
        error: 'Unable to connect to Motoko LLM server. Please ensure the server is running at 192.168.1.12:8000',
      });
    }

    if (error instanceof Error && error.message.includes('ECONNREFUSED')) {
      return res.status(503).json({
        error: 'Connection refused by Motoko LLM server. Please check if the server is running and accessible.',
      });
    }

    return res.status(500).json({
      error: 'Internal server error while building deck',
    });
  }
}

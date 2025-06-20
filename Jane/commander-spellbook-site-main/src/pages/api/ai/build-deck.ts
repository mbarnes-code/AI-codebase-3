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

// Simple rate limiting store (in production, use Redis or similar)
const rateLimitStore = new Map<string, { count: number; resetTime: number }>();
const RATE_LIMIT_PER_MINUTE = 10;
const RATE_LIMIT_WINDOW = 60 * 1000; // 1 minute in milliseconds

function getRateLimitKey(req: NextApiRequest): string {
  // Use IP address for rate limiting
  const forwarded = req.headers['x-forwarded-for'];
  const ip = forwarded ? (Array.isArray(forwarded) ? forwarded[0] : forwarded.split(',')[0]) : req.socket.remoteAddress;
  return `rate_limit:${ip}`;
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

  // Validate required fields
  if (!commander || !commander.trim()) {
    return res.status(400).json({ error: 'Commander name is required' });
  }

  try {
    // Use the Motoko LLM server URL
    const llmUrl = process.env.NEXT_PUBLIC_LLM_SERVER_URL || 'http://motoko:8000';

    // Compose prompt for LLM
    const prompt = `Build a 100-card Commander deck for commander: ${commander}\nFormat: ${format}\nStrategy: ${strategy_focus}\nBudget: ${budget_range}`;

    // Call Motoko LLM server's /generate endpoint
    const response = await fetch(`${llmUrl}/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        prompt,
        model: 'llama2', // or another model as needed
        options: {},
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Motoko LLM error (${response.status}):`, errorText);
      return res.status(response.status).json({ error: `Motoko LLM error: ${response.statusText}` });
    }

    const llmData = await response.json();
    // You may need to parse llmData.response into the DeckBuildResponse format expected by the frontend
    // For now, return the raw LLM response for debugging
    return res.status(200).json({
      commander,
      format,
      recommended_cards: [],
      analysis: {
        strategy: strategy_focus,
        synergies: [],
        power_level: '',
        estimated_cost: '',
        deck_slots: [],
        mana_curve: {},
        color_distribution: {},
      },
      phase: 'llm-response',
      status: 'ok',
      llm_raw: llmData.response,
    } as any);
  } catch (error) {
    console.error('Error calling AI deck builder:', error);

    if (error instanceof TypeError && error.message.includes('fetch')) {
      return res.status(503).json({
        error: 'Unable to connect to the deck building service',
      });
    }

    return res.status(500).json({
      error: 'Internal server error while building deck',
    });
  }
}

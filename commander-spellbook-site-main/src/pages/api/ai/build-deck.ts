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
  res: NextApiResponse<DeckBuildResponse | { error: string }>
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

  const { commander, format = 'commander', strategy_focus = 'balanced', budget_range = 'casual' }: DeckBuildRequest = req.body;

  // Validate required fields
  if (!commander || !commander.trim()) {
    return res.status(400).json({ error: 'Commander name is required' });
  }

  try {
    // Use the correct AI service URL - you may need to update this environment variable
    const backendUrl = process.env.NEXT_PUBLIC_AI_SERVICE_URL || process.env.NEXT_PUBLIC_EDITOR_BACKEND_URL || 'http://localhost:8000';
    
    console.log(`Calling AI deck builder for commander: ${commander}`);
    
    // Call the Django backend AI deck builder endpoint
    const response = await fetch(`${backendUrl}/ai/build-deck`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        commander: commander.trim(),
        format,
        strategy_focus,
        budget_range,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Backend error (${response.status}):`, errorText);
      
      if (response.status === 404) {
        return res.status(404).json({ error: `Commander "${commander}" not found` });
      }
      
      if (response.status === 503) {
        return res.status(503).json({ error: 'AI service is currently unavailable' });
      }
      
      return res.status(response.status).json({ 
        error: `Backend error: ${response.statusText}` 
      });
    }

    const deckData: DeckBuildResponse = await response.json();
    
    console.log(`Successfully generated deck for ${commander}`);
    
    // Add rate limit headers
    res.setHeader('X-RateLimit-Limit', RATE_LIMIT_PER_MINUTE);
    res.setHeader('X-RateLimit-Remaining', rateLimitResult.remaining);
    res.setHeader('X-RateLimit-Reset', Math.ceil((Date.now() + RATE_LIMIT_WINDOW) / 1000));
    
    return res.status(200).json(deckData);

  } catch (error) {
    console.error('Error calling AI deck builder:', error);
    
    if (error instanceof TypeError && error.message.includes('fetch')) {
      return res.status(503).json({ 
        error: 'Unable to connect to the deck building service' 
      });
    }
    
    return res.status(500).json({ 
      error: 'Internal server error while building deck' 
    });
  }
}
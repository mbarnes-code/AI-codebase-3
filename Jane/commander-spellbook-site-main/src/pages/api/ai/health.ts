// src/pages/api/ai/health.ts

import type { NextApiRequest, NextApiResponse } from 'next';

interface HealthResponse {
  jane_status: 'ok';
  motoko_status: 'connected' | 'disconnected' | 'error';
  motoko_url: string;
  timestamp: string;
  error?: string;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<HealthResponse>
) {
  // Only allow GET requests
  if (req.method !== 'GET') {
    return res.status(405).json({
      jane_status: 'ok',
      motoko_status: 'error',
      motoko_url: '',
      timestamp: new Date().toISOString(),
      error: 'Method not allowed'
    });
  }

  const llmUrl = process.env.NEXT_PUBLIC_LLM_SERVER_URL || 'http://192.168.1.12:8000';

  try {
    // Test connection to Motoko LLM server
    const response = await fetch(`${llmUrl}/health`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      // Set a short timeout for health checks
      signal: AbortSignal.timeout(5000), // 5 second timeout
    });

    if (response.ok) {
      const motokoHealth = await response.json();
      return res.status(200).json({
        jane_status: 'ok',
        motoko_status: 'connected',
        motoko_url: llmUrl,
        timestamp: new Date().toISOString(),
      });
    } else {
      return res.status(200).json({
        jane_status: 'ok',
        motoko_status: 'error',
        motoko_url: llmUrl,
        timestamp: new Date().toISOString(),
        error: `Motoko server returned ${response.status}: ${response.statusText}`
      });
    }
  } catch (error) {
    console.error('Health check error:', error);
    
    let errorMessage = 'Unknown error';
    if (error instanceof Error) {
      errorMessage = error.message;
    }

    return res.status(200).json({
      jane_status: 'ok',
      motoko_status: 'disconnected',
      motoko_url: llmUrl,
      timestamp: new Date().toISOString(),
      error: `Cannot connect to Motoko: ${errorMessage}`
    });
  }
}

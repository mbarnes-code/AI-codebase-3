# Updated spellbook/views/ai_deck_builder.py - Phase 1 Step 2

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
import requests
import json

# AI Service Configuration
AI_SERVICE_URL = "http://localhost:8001"  # Your FastAPI service
AI_TIMEOUT = 30  # seconds

@api_view(['POST'])
@permission_classes([AllowAny])
def ai_deck_builder(request):
    """
    Phase 1 Step 2: AI deck builder with FastAPI connection
    Input: {'commander': 'card_name'}
    Output: AI analysis and deck suggestions from your FastAPI service
    """
    commander = request.data.get('commander')
    
    if not commander:
        return Response({'error': 'Commander required'}, status=400)
    
    try:
        # Phase 2: Call your FastAPI AI service
        ai_response = call_ai_service(commander)
        
        return Response({
            'status': 'Phase 1 Step 2 - AI service connected!',
            'commander': commander,
            'message': f'AI analysis complete for {commander}',
            'phase': 1.2,
            'ai_service_status': 'connected',
            'ai_response': ai_response,
            'next_steps': [
                'Implement card recommendation logic',
                'Add synergy analysis with Qdrant',
                'Integrate combo detection',
                'Build 100-card optimization'
            ]
        })
        
    except Exception as e:
        # Fallback to Phase 1 behavior if AI service is down
        return Response({
            'status': 'Phase 1 fallback - AI service unavailable',
            'commander': commander,
            'message': f'Building deck for {commander}... (AI service offline)',
            'phase': 1.0,
            'ai_service_status': 'offline',
            'error': str(e),
            'fallback_response': get_fallback_response(commander)
        })

def call_ai_service(commander):
    """
    Call your FastAPI AI service for deck analysis
    """
    try:
        # Prepare payload for your AI service
        payload = {
            'commander': commander,
            'analysis_type': 'deck_builder',
            'phase': 1
        }
        
        # Call FastAPI service
        response = requests.post(
            f"{AI_SERVICE_URL}/analyze-commander",
            json=payload,
            timeout=AI_TIMEOUT,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"AI service returned {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionError:
        raise Exception("Cannot connect to AI service - is it running?")
    except requests.exceptions.Timeout:
        raise Exception("AI service timeout - analysis taking too long")
    except Exception as e:
        raise Exception(f"AI service error: {str(e)}")

def get_fallback_response(commander):
    """
    Fallback response when AI service is unavailable
    """
    return {
        'analysis': f'Basic analysis for {commander}',
        'recommendations': [
            'Sol Ring - Universal mana acceleration',
            'Command Tower - Reliable mana fixing',
            'Lightning Greaves - Commander protection'
        ],
        'synergies': [
            f'{commander} works well with creatures',
            'Consider tribal synergies',
            'Add card draw and ramp'
        ],
        'note': 'This is a fallback response - connect AI service for full analysis'
    }
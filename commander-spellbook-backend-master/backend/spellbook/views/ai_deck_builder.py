from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter
import logging

from ..services.ai_service import ai_service

logger = logging.getLogger(__name__)

@extend_schema(
    operation_id='ai_build_deck',
    description='Build an optimized Commander deck using AI',
    parameters=[
        OpenApiParameter(
            name='commander',
            description='Commander card name',
            required=True,
            type=str
        ),
        OpenApiParameter(
            name='format',
            description='Deck format (default: commander)',
            required=False,
            type=str
        ),
    ],
    responses={
        200: {
            'description': 'Deck built successfully',
            'example': {
                'commander': 'Atraxa, Praetors\' Voice',
                'format': 'commander',
                'recommended_cards': ['Sol Ring', 'Command Tower'],
                'analysis': {
                    'strategy': 'Proliferate and value',
                    'synergies': [],
                    'power_level': '8/10'
                }
            }
        },
        400: {'description': 'Invalid request'},
        500: {'description': 'AI service unavailable'}
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def ai_build_deck(request):
    """AI Deck Builder endpoint - connects Django to FastAPI AI service"""
    
    try:
        # Get parameters from request
        commander = request.data.get('commander')
        format_type = request.data.get('format', 'commander')
        
        # Validate input
        if not commander:
            return Response(
                {'error': 'Commander name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"AI deck build request: commander={commander}, format={format_type}")
        
        # Check if AI service is available
        if not ai_service.health_check():
            return Response(
                {'error': 'AI service is currently unavailable'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Call AI service
        deck_data = ai_service.build_deck(commander, format_type)
        
        if deck_data is None:
            return Response(
                {'error': 'Failed to generate deck recommendations'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Return the AI-generated deck
        return Response(deck_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in ai_build_deck: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
from django.urls import include, path, re_path
from common.hybridrouter import HybridRouter
from . import views
from .views.ai_deck_builder import ai_build_deck

router = HybridRouter()
router.register(r'variants', views.VariantViewSet, basename='variants')
router.register(r'features', views.FeatureViewSet, basename='features')
router.register(r'cards', views.CardViewSet, basename='cards')
router.register(r'templates', views.TemplateViewSet, basename='templates')
router.register(r'variant-suggestions', views.VariantSuggestionViewSet, basename='variant-suggestions')
router.register(r'variant-update-suggestions', views.VariantUpdateSuggestionViewSet, basename='variant-update-suggestions')
router.register(r'variant-aliases', views.VariantAliasViewSet, basename='variant-aliases')
router.add_api_view(r'find-my-combos', re_path(r'find-my-combos', views.FindMyCombosView.as_view(), name='find-my-combos'))
router.add_api_view(r'estimate-bracket', re_path(r'estimate-bracket', views.EstimateBracketView.as_view(), name='estimate-bracket'))
router.add_api_view(r'ai-deck-builder', path('ai-deck-builder', views.ai_deck_builder, name='ai-deck-builder'))
router.add_api_view('ai-build-deck', path('ai/build-deck', ai_build_deck, name='ai-build-deck'))

urlpatterns = [
    path('', include(router.urls))
]

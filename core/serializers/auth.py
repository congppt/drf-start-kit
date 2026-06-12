from djangorestframework_camel_case.settings import api_settings
from djangorestframework_camel_case.util import camelize
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class TokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        
        # camelize token claims with similar rules as DRF JSON renderer
        token.payload = camelize(token.payload, **api_settings.JSON_UNDERSCOREIZE)

        return token
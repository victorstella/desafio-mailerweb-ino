import os

from rest_framework import authentication
from rest_framework import exceptions


class _APIUser:
    """Objeto similar a `User` usado para autenticação via token único."""

    @property
    def is_authenticated(self):
        """Retorna True para sinalizar usuário autenticado pelo token."""
        return True


class BearerTokenAuthentication(authentication.BaseAuthentication):
    """Autenticação simples via Bearer token definido em `API_TOKEN`.

    - Se o header Authorization estiver ausente, retorna None (permite views públicas).
    - Se presente, valida formato e compara com `API_TOKEN`.
    """

    def authenticate(self, request):
        """Verifica header Authorization e retorna um usuário, se válido."""
        auth = request.headers.get('Authorization') or request.META.get('HTTP_AUTHORIZATION')
        if not auth:
            # Sem credenciais: não falha aqui para permitir acesso público onde aplicável.
            return None
        parts = auth.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            raise exceptions.AuthenticationFailed('Cabeçalho de autorização inválido')
        token = parts[1]
        expected = os.environ.get('API_TOKEN')
        if not expected:
            raise exceptions.AuthenticationFailed('Token de API não configurado no servidor')
        if token != expected:
            raise exceptions.AuthenticationFailed('Token de API inválido')
        return (_APIUser(), token)

    def authenticate_header(self, request):
        return 'Bearer'

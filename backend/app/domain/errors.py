"""Erros de domínio. Não dependem de framework — a camada HTTP os traduz para status."""


class DomainError(Exception):
    """Erro base do domínio."""


class EntityNotFound(DomainError):
    """Entidade referenciada não existe."""


class InvalidState(DomainError):
    """Operação viola uma invariante do domínio."""


class AuthenticationError(DomainError):
    """Credenciais ausentes ou inválidas."""


class AuthorizationError(DomainError):
    """Usuário autenticado, mas sem permissão para a operação."""

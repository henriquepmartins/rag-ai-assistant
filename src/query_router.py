"""Roteamento de queries baseado em intenção."""

import logging
import re
from typing import Dict, Any, Optional

from src.config import Config

logger = logging.getLogger(__name__)


class QueryRouter:
    """Detecta intenção e direciona para handlers apropriados."""

    SUPPORT_EMAIL = "suporte@emvidros.com.br"
    SUPPORT_RESPONSE = """Para consultas sobre entrega de produtos, status de pedidos ou situação de entrega, por favor entre em contato com nosso suporte:

Email: {email}

Nossa equipe terá prazer em ajudá-lo com informações específicas sobre seu pedido e entrega.

Para agilizar o atendimento, tenha em mãos:
- Número do pedido
- CPF/CNPJ do cadastro
- Data da compra
"""

    # Padrões para detectar queries de entrega
    DELIVERY_PATTERNS = [
        r"entrega",
        r"pedido",
        r"envio",
        r"rastreamento",
        r"rastrear",
        r"status",
        r"saiu para entrega",
        r"quando chega",
        r"quando vai chegar",
        r"demora",
        r"atraso",
        r"prazo de entrega",
        r"frete",
        r"transportadora",
        r"correio",
        r"jadlog",
        r"meu produto",
        r"minha compra",
        r"já foi enviado",
        r"quanto tempo",
        r"onde está",
    ]

    # Padrões de produto (não devem acionar suporte)
    PRODUCT_PATTERNS = [
        r"quais produtos",
        r"o que vende",
        r"tem vidro",
        r"tem espelho",
        r"preço",
        r"valor",
        r"catálogo",
        r"lista de produtos",
    ]

    def __init__(self):
        self._delivery_regex = re.compile(
            r"|".join(self.DELIVERY_PATTERNS),
            re.IGNORECASE
        )
        self._product_regex = re.compile(
            r"|".join(self.PRODUCT_PATTERNS),
            re.IGNORECASE
        )

    def _is_delivery_query(self, message: str) -> bool:
        """Verifica se mensagem é sobre entrega/pedido."""
        has_delivery = bool(self._delivery_regex.search(message))
        has_product = bool(self._product_regex.search(message))

        # Tem padrão de entrega mas NÃO tem padrão de produto
        return has_delivery and not has_product

    def route(self, message: str) -> Optional[Dict[str, Any]]:
        """Direciona mensagem para handler apropriado."""
        if self._is_delivery_query(message):
            logger.info(f"Routing to support: {message[:50]}...")
            return {
                "response": self.SUPPORT_RESPONSE.format(email=self.SUPPORT_EMAIL),
                "routed_to": "support",
                "success": True,
            }

        return None

    def get_support_info(self) -> Dict[str, str]:
        """Retorna informações de contato do suporte."""
        return {
            "email": self.SUPPORT_EMAIL,
            "phone": "",
        }

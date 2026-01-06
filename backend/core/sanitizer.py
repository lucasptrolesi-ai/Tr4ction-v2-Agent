# backend/core/sanitizer.py
"""
Sanitizador de Input - Proteção contra XSS e injeção

Módulo leve para sanitizar inputs de usuário antes de processamento.
NÃO usa dependências pesadas - implementação simples e segura.
"""

import re
import html
from typing import Optional


# ============================================================
# PADRÕES PERIGOSOS (regex compilados para performance)
# ============================================================

# Tags de script e event handlers
SCRIPT_PATTERN = re.compile(
    r'<\s*script[^>]*>.*?</\s*script\s*>|'  # <script>...</script>
    r'<\s*script[^>]*>|'                      # <script> sem fechar
    r'javascript\s*:',                         # javascript: URLs
    re.IGNORECASE | re.DOTALL
)

# Event handlers HTML (onclick, onerror, etc.)
EVENT_HANDLER_PATTERN = re.compile(
    r'\bon\w+\s*=',  # on* = (onclick, onerror, onload, etc.)
    re.IGNORECASE
)

# Tags HTML perigosas (não <script> pois já está acima)
DANGEROUS_TAGS_PATTERN = re.compile(
    r'<\s*(iframe|object|embed|form|input|button|style|link|meta|base)[^>]*>',
    re.IGNORECASE
)

# Data URLs que podem conter código
DATA_URL_PATTERN = re.compile(
    r'data\s*:\s*(text/html|application/javascript)',
    re.IGNORECASE
)


# ============================================================
# FUNÇÕES DE SANITIZAÇÃO
# ============================================================

def sanitize_text(text: Optional[str], max_length: int = 10000) -> str:
    """
    Sanitiza texto de input contra XSS e injeção.
    
    Operações realizadas:
    1. Remove tags <script>
    2. Remove event handlers (onclick, etc.)
    3. Remove tags HTML perigosas
    4. Remove data: URLs perigosos
    5. Escapa caracteres HTML restantes
    6. Limita tamanho
    
    Args:
        text: Texto a sanitizar
        max_length: Tamanho máximo permitido
        
    Returns:
        Texto sanitizado e seguro
    """
    if not text:
        return ""
    
    # Garante que é string
    text = str(text)
    
    # Limita tamanho antes de processar (proteção DoS)
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove scripts
    text = SCRIPT_PATTERN.sub('', text)
    
    # Remove event handlers
    text = EVENT_HANDLER_PATTERN.sub('', text)
    
    # Remove tags perigosas
    text = DANGEROUS_TAGS_PATTERN.sub('', text)
    
    # Remove data URLs perigosos
    text = DATA_URL_PATTERN.sub('', text)
    
    # Limpa espaços extras resultantes
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def sanitize_html_escape(text: Optional[str]) -> str:
    """
    Escapa HTML completamente (para exibição segura).
    Mais restritivo que sanitize_text().
    
    Útil para inputs que serão exibidos como texto puro.
    """
    if not text:
        return ""
    
    return html.escape(str(text))


def sanitize_for_llm(text: Optional[str], max_length: int = 4000) -> str:
    """
    Sanitiza texto especificamente para envio ao LLM.
    
    Remove conteúdo potencialmente perigoso mas mantém
    formatação básica como markdown.
    
    Args:
        text: Pergunta ou contexto para o LLM
        max_length: Limite para evitar overflow de tokens
        
    Returns:
        Texto sanitizado seguro para processamento LLM
    """
    if not text:
        return ""
    
    text = str(text)
    
    # Limita tamanho (LLMs têm limite de tokens)
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    # Remove scripts e event handlers
    text = SCRIPT_PATTERN.sub('', text)
    text = EVENT_HANDLER_PATTERN.sub('', text)
    
    # Remove prompts de injeção comuns (prompt injection básico)
    injection_patterns = [
        r'ignore\s+previous\s+instructions?',
        r'disregard\s+.*\s+instructions?',
        r'you\s+are\s+now\s+a\s+',
        r'pretend\s+you\s+are\s+',
        r'act\s+as\s+if\s+you\s+',
    ]
    for pattern in injection_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Remove caracteres de controle (exceto newline e tab)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    return text.strip()


def is_safe_input(text: Optional[str]) -> bool:
    """
    Verifica se o input é seguro (sem conteúdo perigoso detectado).
    
    Returns:
        True se o input parece seguro, False se contém padrões perigosos
    """
    if not text:
        return True
    
    text = str(text)
    
    # Verifica padrões perigosos
    if SCRIPT_PATTERN.search(text):
        return False
    if EVENT_HANDLER_PATTERN.search(text):
        return False
    if DANGEROUS_TAGS_PATTERN.search(text):
        return False
    if DATA_URL_PATTERN.search(text):
        return False
    
    return True

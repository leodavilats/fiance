from __future__ import annotations

import logging
import json

from typing import List, Dict, Any

from app.core.config import get_settings

from app.models.recommendation import Allocation
from app.models.enums import RiskProfile

logger = logging.getLogger(__name__)

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-genai não instalado. Execute: pip install google-genai")

SYSTEM_PROMPT = (

    "Você é um analista financeiro CNPI. Explique de forma objetiva, em "

    "português do Brasil, por que a carteira sugerida faz sentido para o "

    "perfil informado. Cite riscos relevantes. Máximo 6 frases. Inclua "

    "disclaimer de que não é recomendação formal."

)

def _format_allocations(allocations: List[Allocation]) -> str:

    lines = []

    for a in allocations:

        lines.append(

            f"- {a.ticker} ({a.sector or 's/setor'}): {a.weight*100:.1f}% | "

            f"R$ {a.invested:.2f} | score {a.score:.1f} | {a.rationale}"

        )

    return "\n".join(lines)

def explain_portfolio(

    allocations: List[Allocation],

    profile: RiskProfile,

    metrics: dict | None = None,

) -> str:

    settings = get_settings()

    if not settings.gemini_api_key or not allocations:

        return ""

    if not GEMINI_AVAILABLE:

        logger.warning("google-generativeai não instalado.")

        return ""

    metrics_txt = ""

    if metrics:

        metrics_txt = (

            f"\nMétricas estimadas: retorno {metrics.get('expected_return', 0)*100:.1f}% a.a., "

            f"volatilidade {metrics.get('volatility', 0)*100:.1f}%, "

            f"Sharpe {metrics.get('sharpe', 0):.2f}."

        )

    user = (

        f"Perfil: {profile.value}.\nCarteira sugerida:\n"

        f"{_format_allocations(allocations)}{metrics_txt}"

    )

    try:

        client = genai.Client(api_key=settings.gemini_api_key)

        response = client.models.generate_content(

            model="gemini-2.0-flash",

            contents=user,

            config=types.GenerateContentConfig(

                system_instruction=SYSTEM_PROMPT,

                temperature=0.3,

                max_output_tokens=400,

            )

        )

        return response.text.strip()

    except Exception as e:

        logger.warning("LLM falhou: %s", e)

        return ""


NEWS_ANALYSIS_PROMPT = """Analise as notícias sobre {company_name} ({symbol}) e retorne APENAS este JSON (sem markdown):

{{
  "sentiment": "positive",
  "score": 7.5,
  "summary": "Breve resumo em 1-2 frases",
  "impact": "high",
  "key_topics": ["tópico1", "tópico2"]
}}

Regras:
- sentiment: "positive", "negative" ou "neutral"
- score: 0.0 a 10.0
- summary: MÁXIMO 100 caracteres
- impact: "high", "medium" ou "low"
- key_topics: até 2 tópicos curtos

Notícias:
{news_text}

JSON puro (sem ```):"""


def analyze_news_sentiment(news_items: List[Dict[str, Any]], symbol: str, company_name: str = "") -> Dict[str, Any]:
    """Analisa sentimento de notícias usando IA."""
    settings = get_settings()
    
    if not settings.gemini_api_key or not news_items:
        return {
            "sentiment": "neutral",
            "score": 5.0,
            "summary": "Sem notícias recentes ou IA não configurada.",
            "impact": "low",
            "key_topics": []
        }
    
    if not GEMINI_AVAILABLE:
        logger.warning("google-generativeai não instalado.")
        return {
            "sentiment": "neutral",
            "score": 5.0,
            "summary": "IA não disponível para análise.",
            "impact": "low",
            "key_topics": []
        }
    
    # Formatar notícias para análise (apenas títulos - funcionam bem!)
    news_text = ""
    for idx, item in enumerate(news_items[:5], 1):  # Reduzido para 5 notícias
        title = item.get('title', '')[:150]
        source = item.get('source', '')
        news_text += f"{idx}. {title} ({source})\n"
    
    prompt = NEWS_ANALYSIS_PROMPT.format(
        company_name=company_name or symbol,
        symbol=symbol,
        news_text=news_text
    )
    
    # Log do que está sendo enviado para a IA
    print("\n" + "="*80)
    print("📤 PROMPT ENVIADO PARA IA (Análise de Notícias)")
    print("="*80)
    print(prompt)
    print("="*80 + "\n")
    
    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        
        # Tentar modelo lite primeiro (quota separada)
        try:
            response = client.models.generate_content(
                model="gemini-flash-lite-latest",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=300,
                )
            )
        except Exception as lite_error:
            # Fallback para modelo principal
            logger.debug(f"Gemini Lite falhou, tentando Flash: {lite_error}")
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=300,
                )
            )
        
        # Extrair JSON da resposta
        result_text = response.text.strip()
        
        # Log da resposta recebida
        print("\n" + "="*80)
        print("📥 RESPOSTA RECEBIDA DA IA")
        print("="*80)
        print(result_text)
        print("="*80 + "\n")
        
        # Verificar se resposta está vazia ou truncada
        if not result_text or len(result_text) < 20:
            logger.warning("Resposta vazia ou muito curta, usando fallback")
            raise ValueError("Resposta vazia ou muito curta")
        
        # Limpar marcadores de código
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        # Remover texto antes/depois do JSON
        start_idx = result_text.find('{')
        end_idx = result_text.rfind('}')
        if start_idx == -1 or end_idx == -1:
            logger.warning(f"JSON não encontrado. Resposta completa: {result_text[:500]}")
            raise ValueError("JSON não encontrado na resposta")
        
        result_text = result_text[start_idx:end_idx+1]
        
        # Corrigir números decimais incompletos (3. -> 3.0)
        import re
        result_text = re.sub(r':\s*(\d+)\.\s*([,\}])', r': \1.0\2', result_text)
        
        try:
            result = json.loads(result_text)
        except json.JSONDecodeError:
            # Tentar limpar aspas problemáticas e espaços
            result_text = result_text.replace("'", '"')
            # Remover quebras de linha dentro de strings
            result_text = re.sub(r'\n\s+', ' ', result_text)
            result = json.loads(result_text)
        
        # Validar e normalizar campos
        result["sentiment"] = str(result.get("sentiment", "neutral")).lower()
        if result["sentiment"] not in ["positive", "negative", "neutral"]:
            result["sentiment"] = "neutral"
        
        result["score"] = max(0.0, min(10.0, float(result.get("score", 5.0))))
        result["summary"] = str(result.get("summary", ""))[:500]  # Limitar tamanho
        
        result["impact"] = str(result.get("impact", "low")).lower()
        if result["impact"] not in ["high", "medium", "low"]:
            result["impact"] = "low"
        
        result["key_topics"] = [str(t)[:50] for t in (result.get("key_topics", []) or [])[:3]]
        
        return result
        
    except json.JSONDecodeError as e:
        logger.warning(f"Erro ao parsear JSON da análise de notícias: {e}")
        logger.warning(f"Resposta recebida: {result_text[:300]}")
        # Fallback: análise básica baseada em contagem
        pos_count = sum(1 for item in news_items if any(word in item.get('title', '').lower() for word in ['lucro', 'crescimento', 'alta', 'positivo', 'recorde', 'aprovação']))
        neg_count = sum(1 for item in news_items if any(word in item.get('title', '').lower() for word in ['prejuízo', 'queda', 'crise', 'negativo', 'perda', 'investigação']))
        score = 5.0 + (pos_count - neg_count) * 0.5
        return {
            "sentiment": "positive" if score > 6 else "negative" if score < 4 else "neutral",
            "score": max(0.0, min(10.0, score)),
            "summary": f"Análise automática de {len(news_items)} notícias. Sentimento geral baseado em palavras-chave.",
            "impact": "medium",
            "key_topics": []
        }
    except Exception as e:
        logger.warning(f"Erro na análise de notícias com IA: {e}")
        return {
            "sentiment": "neutral",
            "score": 5.0,
            "summary": "Erro ao processar análise de notícias.",
            "impact": "low",
            "key_topics": []
        }
    except Exception as e:
        logger.warning(f"Erro na análise de notícias com IA: {e}")
        return {
            "sentiment": "neutral",
            "score": 5.0,
            "summary": "Erro ao analisar notícias.",
            "impact": "low",
            "key_topics": []
        }



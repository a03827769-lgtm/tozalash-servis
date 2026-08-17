"""
Tozalash Servis - AI Agentlar va Veb-Skreping (Tasks 54, 55)
- LangGraph yordamida ko'p agentli muloqot (Multi-Agent System).
- Raqobatchilar tahlili uchun avtomatlashtirilgan web scraping.
"""

import asyncio
import os
import json
from typing import TypedDict, Annotated, Sequence, List
import operator
from loguru import logger

try:
    import httpx
except ImportError:
    httpx = None
    logger.warning("httpx o'rnatilmagan.")

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
    logger.warning("BeautifulSoup o'rnatilmagan. 'pip install beautifulsoup4' qiling.")

try:
    from langgraph.graph import StateGraph, END
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
except ImportError:
    logger.warning("LangGraph o'rnatilmagan. 'pip install langgraph langchain-core' qiling.")
    # Fallback sinflar, kod qulab tushmasligi uchun
    class BaseMessage: pass
    class HumanMessage(BaseMessage): 
        def __init__(self, content): self.content = content
    class AIMessage(BaseMessage): 
        def __init__(self, content): self.content = content
    class StateGraph:
        def __init__(self, *args, **kwargs): pass
        def add_node(self, *args, **kwargs): pass
        def set_entry_point(self, *args, **kwargs): pass
        def add_edge(self, *args, **kwargs): pass
        def compile(self): return None
    END = "END"

from config import GEMINI_API_KEY
from gemini_rotator import gemini_rotator

# ================================================
# 1. STATE DEFINITION
# ================================================

class AgentState(TypedDict):
    """Agentlar o'rtasida uzatiladigan holat"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    competitor_urls: List[str]
    scraped_data: str
    analysis_result: str


# ================================================
# 2. VEB-SKREPPER (Task 55)
# ================================================

async def scrape_competitors(urls: List[str]) -> str:
    """Raqobatchilar veb-saytlaridan narxlarni yig'ish (Scraping)"""
    logger.info(f"Veb-skreping boshlandi: {len(urls)} ta sayt.")
    results = []
    
    async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
        for url in urls:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    # Saytdagi barcha matnni ajratib olish va tozalash
                    text_content = soup.get_text(separator=' ', strip=True)
                    
                    # Faqat birinchi 1000 ta belgini olish (xotirani tejash uchun)
                    snippet = text_content[:1000]
                    results.append(f"Sayt: {url}\nMa'lumot: {snippet}...\n")
                else:
                    results.append(f"Sayt: {url}\nXatolik: {response.status_code}\n")
            except Exception as e:
                logger.error(f"Skreping xatosi ({url}): {e}")
                results.append(f"Sayt: {url}\nXatolik: {str(e)}\n")
                
    if not results:
        return "Raqobatchilar saytidan ma'lumot topilmadi."
    return "\n".join(results)


# ================================================
# 3. LANGGRAPH NODELARI (Task 54)
# ================================================

async def researcher_node(state: AgentState):
    """Raqobatchilar bo'yicha ma'lumot yig'uvchi agent"""
    logger.info("Agent: Researcher (Ma'lumot yig'moqda...)")
    
    urls = state.get("competitor_urls", [])
    if not urls:
        urls = [
            "https://example.com/cleaning-uz", # Namuna saytlar
            "https://example.com/tozalash-xizmati"
        ]
        
    scraped_data = await scrape_competitors(urls)
    
    return {
        "scraped_data": scraped_data,
        "messages": [AIMessage(content="Veb-skreping muvaffaqiyatli yakunlandi.")]
    }

async def analyzer_node(state: AgentState):
    """Yig'ilgan ma'lumotlarni tahlil qilib, biznes qaror qabul qiluvchi agent"""
    logger.info("Agent: Analyzer (Tahlil qilmoqda...)")
    
    scraped_data = state.get("scraped_data", "")
    if not scraped_data:
        return {"analysis_result": "Tahlil qilish uchun ma'lumot yo'q."}

    # Gemini orqali tahlil qilish
    prompt = f"""
Siz Tozalash Servisi biznes analitikisiz.
Quyida raqobatchilar veb-saytlaridan olingan ma'lumotlar keltirilgan:

{scraped_data}

Vazifa: Ushbu ma'lumotlarga asoslanib, raqobatchilar narxlarini, xizmat turlarini tahlil qiling
va bizning biznesimiz uchun eng yaxshi strategiyani (narxni tushirish/oshirish, aksiyalar) tavsiya qiling.
O'zbek tilida qisqa va aniq hisobot yozing.
"""

    try:
        import google.generativeai as genai
        # Gemini sozlash
        key = gemini_rotator.get_next_key() or GEMINI_API_KEY
        if key:
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = await asyncio.to_thread(model.generate_content, prompt)
            analysis = response.text
        else:
            analysis = "API kaliti yo'q, LLM tahlili o'tkazilmadi."
    except Exception as e:
        logger.error(f"Analyzer xatosi: {e}")
        analysis = f"Tahlil paytida texnik xatolik yuz berdi: {e}"

    return {
        "analysis_result": analysis,
        "messages": [AIMessage(content="Raqobatchilar ma'lumotlari tahlil qilindi.")]
    }


# ================================================
# 4. LANGGRAPH GRAPH DEFINITION
# ================================================

def build_competitor_analysis_graph():
    """Agentlar tarmog'ini yaratish"""
    try:
        workflow = StateGraph(AgentState)

        # Nodlarni qo'shish
        workflow.add_node("researcher", researcher_node)
        workflow.add_node("analyzer", analyzer_node)

        # Chegaralarni (edges) o'rnatish
        workflow.set_entry_point("researcher")
        workflow.add_edge("researcher", "analyzer")
        workflow.add_edge("analyzer", END)

        # Kompilyatsiya qilish
        return workflow.compile()
    except Exception as e:
        logger.error(f"Graph tuzishda xatolik: {e}")
        return None


# ================================================
# 5. ASOSIY ISHGA TUSHIRISH FUNKSIYASI
# ================================================

async def run_competitor_analysis(urls: List[str] = None) -> str:
    """Tizimning istalgan joyidan chaqiriladigan yagona interfeys"""
    graph = build_competitor_analysis_graph()
    if not graph:
        return "LangGraph tizimi o'rnatilmagan yoki ishlamayapti."

    initial_state = {
        "messages": [HumanMessage(content="Raqobatchilarni tahlil qilishni boshla.")],
        "competitor_urls": urls or [],
        "scraped_data": "",
        "analysis_result": ""
    }

    try:
        logger.info("Ko'p agentli LangGraph tizimi ishga tushdi...")
        # Asinxron ravishda graphni ishga tushirish
        final_state = await graph.ainvoke(initial_state)
        logger.info("LangGraph tizimi o'z ishini yakunladi.")
        return final_state.get("analysis_result", "Natija topilmadi.")
    except Exception as e:
        logger.error(f"Ko'p agentli tizim ishida xatolik: {e}")
        return f"Xatolik: {e}"

if __name__ == "__main__":
    # Mustaqil sinab ko'rish uchun
    async def test():
        print("=== LangGraph Test ===")
        res = await run_competitor_analysis(["https://cleaner.uz", "https://tozalash.uz"])
        print(f"NATIJA:\n{res}")
        
    asyncio.run(test())

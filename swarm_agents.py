import json
import os
from typing import Optional, Dict
from loguru import logger
from gemini_rotator import rotator

class DynamicAgent:
    """A generic agent class that dynamically inherits its role from master prompts."""
    def __init__(self, name: str, system_prompt: str, rotator_instance):
        self.name = name
        self.system_prompt = system_prompt
        self.rotator = rotator_instance

    async def handle(self, message: str, context: dict = None, extra_instructions: str = "") -> Optional[str]:
        ctx_str = f"Kontekst: {json.dumps(context, ensure_ascii=False)}" if context else ""
        full_prompt = f"{self.system_prompt}\n{extra_instructions}\n{ctx_str}\n\nXabar: {message}\nJavobingiz:"
        try:
            resp = await self.rotator.ask(full_prompt)
            if resp and len(resp.strip()) > 0:
                return resp
        except Exception as e:
            logger.warning(f"Agent {self.name} generation xatosi: {e}")
        return None

class AgentRegistry:
    """Loads and manages all specialized agents."""
    def __init__(self, prompts_source="master_prompts.json"):
        self.agents = {}
        self.rotator = rotator
        
        if isinstance(prompts_source, dict):
            for name, prompt in prompts_source.items():
                if isinstance(prompt, str):
                    self.agents[name] = DynamicAgent(name, prompt, self.rotator)
            logger.success(f"AgentRegistry: {len(self.agents)} ta agent lug'atdan yuklandi.")
        elif isinstance(prompts_source, str) and os.path.exists(prompts_source):
            try:
                with open(prompts_source, 'r', encoding='utf-8') as f:
                    prompts = json.load(f)
                    for name, prompt in prompts.items():
                        if isinstance(prompt, str):
                            self.agents[name] = DynamicAgent(name, prompt, self.rotator)
                logger.success(f"AgentRegistry: {len(self.agents)} ta agent {prompts_source} faylidan yuklandi.")
            except Exception as e:
                logger.error(f"AgentRegistry yuklashda xato: {e}")
        
        # Ensure default agents exist
        if "master_router" not in self.agents:
            self.agents["master_router"] = DynamicAgent(
                "master_router",
                "Siz Tozalash Servisining bosh boshqaruvchisisiz. Xabarni turiga qarab yo'naltiring (sales, support, urgent, complain).",
                self.rotator
            )
        if "support_agent" not in self.agents:
            self.agents["support_agent"] = DynamicAgent(
                "support_agent",
                "Siz Tozalash Servisi mijozlarga xizmat ko'rsatish mutaxassisisiz. Xushmuomala va aniq javob bering.",
                self.rotator
            )
        if "sales_agent" not in self.agents:
            self.agents["sales_agent"] = DynamicAgent(
                "sales_agent",
                "Siz Tozalash Servisi savdo menejerisiz. Narxlarni tushuntiring va buyurtma rasmiylashtirishga yordam bering.",
                self.rotator
            )

    def get_agent(self, name: str) -> Optional[DynamicAgent]:
        return self.agents.get(name) or self.agents.get("support_agent")

class SwarmOrchestrator:
    """Coordinates the swarm agents."""
    def __init__(self, prompts_data=None):
        source = prompts_data if prompts_data else "master_prompts.json"
        self.registry = AgentRegistry(source)
        self.master_router = self.registry.get_agent("master_router")
        self.qa_agent = self.registry.get_agent("qa_agent")
        
        # Initialize Memory (AgentDB Logic)
        try:
            from memory_manager import memory_db
            self.memory = memory_db
        except Exception as e:
            self.memory = None

    async def process_message(self, message: str, context: dict = None, language: str = "uz") -> Optional[str]:
        logger.info(f"Swarm: Analyzing message: '{message[:80]}'")
        
        if not self.master_router:
            return None
            
        # 0. Memory Retrieval (AgentDB Reasoning Pattern)
        past_experiences = ""
        if self.memory:
            try:
                similar_memories = self.memory.retrieve_with_reasoning(message, n_results=2)
                if similar_memories:
                    past_experiences = "Oldingi tajriba (Memory):\n" + "\n".join([m['content'] for m in similar_memories])
                    logger.info(f"Swarm: Injected {len(similar_memories)} past memories into context.")
            except Exception:
                pass
        
        # Inject memory into context
        if not context:
            context = {}
        if past_experiences:
            context["past_memory"] = past_experiences
            
        # 1. Routing
        routing_instruction = "Javobingiz FAKAT BITTA SO'Z bo'lishi shart (masalan: sales_agent, support_agent, vision_agent)."
        intent = await self.master_router.handle(message, context, routing_instruction)
        
        target_agent_name = "support_agent"
        if intent:
            cleaned_intent = intent.strip().lower()
            if cleaned_intent in self.registry.agents:
                target_agent_name = cleaned_intent
            elif "sales" in cleaned_intent:
                target_agent_name = "sales_agent"
            elif "vision" in cleaned_intent:
                target_agent_name = "vision_agent"
            elif "urgent" in cleaned_intent:
                target_agent_name = "priority_agent"
            
        logger.info(f"Swarm: Routed to -> {target_agent_name}")
        
        # 2. Drafting
        target_agent = self.registry.get_agent(target_agent_name) or self.registry.get_agent("support_agent")
        draft_response = await target_agent.handle(message, context)
        
        if not draft_response:
            return None
            
        logger.info(f"Swarm: Draft generated by {target_agent.name}")
        
        # 3. QA / Validation
        final_response = draft_response
        if self.qa_agent:
            qa_instruction = f"Tekshiruvchi: Mijoz '{message}' yozdi. Agent ({target_agent.name}) javobi: '{draft_response}'. Agar xato yoki qo'pollik bo'lsa to'g'rilab, yakuniy JSON qaytaring. Format: {{\"action\": \"{target_agent.name}\", \"language\": \"{language}\", \"message\": \"yakuniy javob\", \"new_state\": \"idle\"}}"
            final_json = await self.qa_agent.handle(draft_response, None, qa_instruction)
            if final_json:
                logger.success("Swarm: QA validated response.")
                final_response = final_json
            
        # 4. Store Pattern to Memory (Learning)
        if self.memory and draft_response:
            try:
                self.memory.store_pattern(
                    user_query=message,
                    agent_name=target_agent_name,
                    response=draft_response,
                    success=True
                )
            except Exception:
                pass
            
        return final_response

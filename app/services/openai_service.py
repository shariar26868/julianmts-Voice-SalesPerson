from openai import AsyncOpenAI
from app.config.settings import settings
from typing import List, Dict, Any, Optional
import json

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


class OpenAIService:
    """Handle multi-agent conversation using OpenAI GPT"""
    
    def __init__(self):
        self.model = "gpt-4-turbo-preview"
    
    async def generate_multi_agent_response(
        self,
        conversation_history: List[Dict[str, str]],
        representatives: List[Dict[str, Any]],
        salesperson_data: Dict[str, Any],
        company_data: Dict[str, Any],
        current_message: str,
        speaker: str = "salesperson"
    ) -> Dict[str, Any]:
        """
        Generate response from AI representatives based on conversation context
        
        Returns:
            {
                "responding_rep": "rep_id",
                "response_text": "...",
                "should_interrupt": False,
                "reasoning": "why this rep is responding"
            }
        """
        
        # Build system prompt for orchestrator
        system_prompt = self._build_orchestrator_prompt(
            representatives, salesperson_data, company_data
        )
        
        # Build conversation context
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add conversation history
        for turn in conversation_history[-10:]:  # Last 10 turns for context
            role = "user" if turn["speaker"] == "salesperson" else "assistant"
            messages.append({
                "role": role,
                "content": f"[{turn['speaker_name']}]: {turn['text']}"
            })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": f"[Salesperson]: {current_message}\n\nWho should respond and what should they say?"
        })
        
        # Get response from GPT
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    
    def _build_orchestrator_prompt(
        self,
        representatives: List[Dict[str, Any]],
        salesperson_data: Dict[str, Any],
        company_data: Dict[str, Any]
    ) -> str:
        """Build detailed system prompt for multi-agent orchestration"""
        
        reps_info = "\n".join([
            f"""
            Representative {i+1}:
            - ID: {rep['id']}
            - Name: {rep['name']}
            - Role: {rep['role']}
            - Personality: {', '.join(rep['personality_traits'])}
            - Decision Maker: {rep['is_decision_maker']}
            - Tenure: {rep['tenure_months']} months
            - Notes: {rep.get('notes', 'N/A')}
            """
            for i, rep in enumerate(representatives)
        ])
        
        prompt = f"""
You are an AI orchestrator managing a sales meeting simulation with multiple company representatives.

COMPANY INFORMATION:
- Company: {company_data.get('company_url', 'N/A')}
- Industry: {company_data.get('company_data', {}).get('industry', 'N/A')}
- Size: {company_data.get('company_data', {}).get('company_size', 'N/A')}
- Revenue: {company_data.get('company_data', {}).get('revenue', 'N/A')}

PRODUCT BEING SOLD:
- Product: {salesperson_data.get('product_name', 'N/A')}
- Description: {salesperson_data.get('description', 'N/A')}

REPRESENTATIVES IN THIS MEETING:
{reps_info}

YOUR TASK:
1. Analyze the salesperson's message
2. Decide which representative should respond based on:
   - Their role and expertise
   - Their personality traits
   - Whether salesperson specifically addressed them
   - Natural conversation flow
   - Decision-making authority
3. Generate an authentic response that matches the representative's personality
4. Determine if another rep might interrupt or add to the conversation

RESPONSE RULES:
- If salesperson asks "What do you think, [Name]?" - that specific rep MUST respond
- If discussing budget/financials - CFO is most likely to respond
- If discussing technology - CTO is most likely to respond
- If discussing strategy/vision - CEO is most likely to respond
- Arrogant personalities will be dismissive, ask tough questions
- Soft personalities will be encouraging, helpful
- Cold personalities will be brief, factual, unemotional
- Decision makers have final say on commitments

OUTPUT FORMAT (JSON):
{{
    "responding_rep_id": "rep_1",
    "responding_rep_name": "John Smith",
    "response_text": "The actual response from this representative",
    "should_interrupt": false,
    "interrupting_rep_id": null,
    "reasoning": "Brief explanation of why this rep is responding"
}}

IMPORTANT:
- Keep responses natural and conversational (2-4 sentences)
- Maintain personality consistency
- Consider power dynamics and hierarchy
- Create realistic business meeting interactions
- If multiple reps want to speak, primary responder goes first
"""
        return prompt
    
    async def generate_top_questions(
        self,
        salesperson_data: Dict[str, Any],
        company_data: Dict[str, Any],
        meeting_goal: str
    ) -> List[str]:
        """Generate top 5 questions salesperson might ask based on context"""
        
        prompt = f"""
Based on this sales scenario, generate exactly 5 strategic questions the salesperson should ask:

PRODUCT/SERVICE:
{salesperson_data.get('product_name')} - {salesperson_data.get('description')}

COMPANY:
- Industry: {company_data.get('company_data', {}).get('industry')}
- Size: {company_data.get('company_data', {}).get('company_size')}
- Current tech: {company_data.get('company_data', {}).get('tech_stack')}

MEETING GOAL:
{meeting_goal}

Generate 5 powerful questions that will:
1. Uncover pain points
2. Qualify the opportunity
3. Build rapport
4. Advance the sale
5. Handle potential objections

Return as JSON:
{{
    "questions": ["question 1", "question 2", "question 3", "question 4", "question 5"]
}}
"""
        
        response = await client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get("questions", [])


# Singleton instance
openai_service = OpenAIService()
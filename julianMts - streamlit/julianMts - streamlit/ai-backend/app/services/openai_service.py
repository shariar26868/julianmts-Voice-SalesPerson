
from openai import AsyncOpenAI
from app.config.settings import settings
from typing import List, Dict, Any, Optional
import json
import re

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
                "responding_rep_id": "rep_id",
                "responding_rep_name": "Name",
                "response_text": "...",
                "should_interrupt": False,
                "reasoning": "why this rep is responding"
            }
        """
        
        try:
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
            print("🤖 Calling OpenAI API...")
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            raw_content = response.choices[0].message.content
            print(f"📝 Raw OpenAI response: {raw_content[:200]}...")
            
            # ✅ FIXED: Better JSON parsing with error handling
            try:
                result = json.loads(raw_content)
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parsing error: {e}")
                # Try to extract JSON from markdown code blocks
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    # Fallback response
                    result = self._create_fallback_response(representatives, current_message)
            
            # ✅ FIXED: Validate response structure
            result = self._validate_and_fix_response(result, representatives)
            
            print(f"✅ Generated response from: {result.get('responding_rep_name')}")
            return result
            
        except Exception as e:
            print(f"❌ OpenAI service error: {e}")
            import traceback
            traceback.print_exc()
            # Return fallback response instead of crashing
            return self._create_fallback_response(representatives, current_message)
    
    def _validate_and_fix_response(
        self, 
        result: Dict[str, Any], 
        representatives: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate and fix AI response structure"""
        
        # Ensure all required fields exist
        required_fields = {
            "responding_rep_id": None,
            "responding_rep_name": None,
            "response_text": "I understand. Could you tell me more?",
            "should_interrupt": False,
            "interrupting_rep_id": None,
            "reasoning": "Default response"
        }
        
        for field, default_value in required_fields.items():
            if field not in result or result[field] is None:
                # Try to infer from other fields
                if field == "responding_rep_id" and not result.get("responding_rep_id"):
                    # Try to match by name
                    rep_name = result.get("responding_rep_name")
                    if rep_name:
                        for rep in representatives:
                            if rep.get("name", "").lower() == rep_name.lower():
                                result["responding_rep_id"] = rep.get("id")
                                break
                    
                    # Still no ID? Use first rep
                    if not result.get("responding_rep_id") and representatives:
                        result["responding_rep_id"] = representatives[0].get("id")
                        result["responding_rep_name"] = representatives[0].get("name")
                
                elif field == "responding_rep_name" and not result.get("responding_rep_name"):
                    # Try to find by ID
                    rep_id = result.get("responding_rep_id")
                    if rep_id:
                        for rep in representatives:
                            if rep.get("id") == rep_id:
                                result["responding_rep_name"] = rep.get("name")
                                break
                    
                    # Still no name? Use first rep
                    if not result.get("responding_rep_name") and representatives:
                        result["responding_rep_name"] = representatives[0].get("name")
                
                else:
                    result[field] = default_value
        
        # Ensure response_text is not empty
        if not result.get("response_text") or result["response_text"].strip() == "":
            result["response_text"] = "That's an interesting point. Let me share my thoughts on that."
        
        return result
    
    def _create_fallback_response(
        self, 
        representatives: List[Dict[str, Any]], 
        message: str
    ) -> Dict[str, Any]:
        """Create a fallback response when AI fails"""
        
        if not representatives:
            return {
                "responding_rep_id": "fallback",
                "responding_rep_name": "Representative",
                "response_text": "I understand. Could you elaborate on that?",
                "should_interrupt": False,
                "interrupting_rep_id": None,
                "reasoning": "Fallback response - AI service unavailable"
            }
        
        # Use first representative as fallback
        first_rep = representatives[0]
        
        # Generate contextual fallback based on personality
        personality = first_rep.get("personality_traits", ["neutral"])[0].lower()
        
        fallback_responses = {
            "angry": "Look, I don't have time for this. Get to the point.",
            "arrogant": "I've seen countless pitches like this. What makes yours different?",
            "soft": "That's interesting. Could you tell me more about that?",
            "cold_hearted": "What are the numbers? I need concrete data.",
            "nice": "I appreciate you sharing that. What else should we know?",
            "analytical": "Can you provide more specific metrics on that?",
            "neutral": "I see. Could you elaborate further?"
        }
        
        response_text = fallback_responses.get(
            personality, 
            "That's an interesting point. Please continue."
        )
        
        return {
            "responding_rep_id": first_rep.get("id"),
            "responding_rep_name": first_rep.get("name"),
            "response_text": response_text,
            "should_interrupt": False,
            "interrupting_rep_id": None,
            "reasoning": f"Fallback response using {personality} personality"
        }
    
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
            - ID: {rep.get('id', 'unknown')}
            - Name: {rep.get('name', 'Unknown')}
            - Role: {rep.get('role', 'Unknown')}
            - Personality: {', '.join(rep.get('personality_traits', ['neutral']))}
            - Decision Maker: {rep.get('is_decision_maker', False)}
            - Tenure: {rep.get('tenure_months', 0)} months
            - Notes: {rep.get('notes', 'N/A')}
            """
            for i, rep in enumerate(representatives)
        ])
        
        # Safe extraction of company data
        company_url = company_data.get('company_url', 'N/A') if company_data else 'N/A'
        company_info = company_data.get('company_data', {}) if company_data else {}
        
        prompt = f"""
You are an AI orchestrator managing a sales meeting simulation with multiple company representatives.

COMPANY INFORMATION:
- Company: {company_url}
- Industry: {company_info.get('industry', 'N/A')}
- Size: {company_info.get('company_size', 'N/A')}
- Revenue: {company_info.get('revenue', 'N/A')}

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

CRITICAL - OUTPUT FORMAT (MUST be valid JSON):
{{
    "responding_rep_id": "exact_id_from_representative_list",
    "responding_rep_name": "exact_name_from_representative_list",
    "response_text": "The actual response from this representative (2-4 sentences, natural conversation)",
    "should_interrupt": false,
    "interrupting_rep_id": null,
    "reasoning": "Brief explanation of why this rep is responding"
}}

IMPORTANT:
- Keep responses natural and conversational (2-4 sentences)
- Maintain personality consistency
- Consider power dynamics and hierarchy
- Create realistic business meeting interactions
- ALWAYS use the EXACT id and name from the representatives list above
- Return ONLY valid JSON, no markdown, no explanations
"""
        return prompt
    
    async def generate_top_questions(
        self,
        salesperson_data: Dict[str, Any],
        company_data: Dict[str, Any],
        meeting_goal: str
    ) -> List[str]:
        """Generate top 5 questions salesperson might ask based on context"""
        
        try:
            # Safe extraction
            company_info = company_data.get('company_data', {}) if company_data else {}
            
            prompt = f"""
Based on this sales scenario, generate exactly 5 strategic questions the salesperson should ask:

PRODUCT/SERVICE:
{salesperson_data.get('product_name', 'Product')} - {salesperson_data.get('description', 'N/A')}

COMPANY:
- Industry: {company_info.get('industry', 'N/A')}
- Size: {company_info.get('company_size', 'N/A')}
- Current tech: {company_info.get('tech_stack', [])}

MEETING GOAL:
{meeting_goal}

Generate 5 powerful questions that will:
1. Uncover pain points
2. Qualify the opportunity
3. Build rapport
4. Advance the sale
5. Handle potential objections

Return ONLY valid JSON with this exact format:
{{
    "questions": [
        "question 1",
        "question 2", 
        "question 3",
        "question 4",
        "question 5"
    ]
}}
"""
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            questions = result.get("questions", [])
            
            # Ensure we have exactly 5 questions
            if len(questions) < 5:
                default_questions = [
                    "What are your current challenges in this area?",
                    "How are you handling this currently?",
                    "What would an ideal solution look like for you?",
                    "What's your timeline for making a decision?",
                    "Who else should be involved in this conversation?"
                ]
                questions.extend(default_questions[len(questions):5])
            
            return questions[:5]
            
        except Exception as e:
            print(f"❌ Error generating questions: {e}")
            # Return default questions
            return [
                "What are your biggest challenges right now?",
                "How does your current solution work?",
                "What would success look like for you?",
                "What's your timeline for implementation?",
                "Who else needs to be part of this decision?"
            ]


# Singleton instance
openai_service = OpenAIService()
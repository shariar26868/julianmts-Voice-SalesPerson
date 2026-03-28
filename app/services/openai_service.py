# from openai import AsyncOpenAI
# from app.config.settings import settings
# from typing import List, Dict, Any, Optional
# import json
# import re

# client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


# class OpenAIService:
#     """Handle multi-agent conversation using OpenAI GPT"""
    
#     def __init__(self):
#         self.model = "gpt-4-turbo-preview"
    
#     async def generate_multi_agent_response(
#         self,
#         conversation_history: List[Dict[str, str]],
#         representatives: List[Dict[str, Any]],
#         salesperson_data: Dict[str, Any],
#         company_data: Dict[str, Any],
#         current_message: str,
#         speaker: str = "salesperson"
#     ) -> Dict[str, Any]:
#         """
#         Generate response from AI representatives based on conversation context
        
#         Returns:
#             {
#                 "responding_rep_id": "rep_id",
#                 "responding_rep_name": "Name",
#                 "response_text": "...",
#                 "should_interrupt": False,
#                 "reasoning": "why this rep is responding"
#             }
#         """
        
#         try:
#             # Build system prompt for orchestrator
#             system_prompt = self._build_orchestrator_prompt(
#                 representatives, salesperson_data, company_data
#             )
            
#             # Build conversation context
#             messages = [
#                 {"role": "system", "content": system_prompt}
#             ]
            
#             # Add conversation history
#             for turn in conversation_history[-10:]:  # Last 10 turns for context
#                 role = "user" if turn["speaker"] == "salesperson" else "assistant"
#                 messages.append({
#                     "role": role,
#                     "content": f"[{turn['speaker_name']}]: {turn['text']}"
#                 })
            
#             # Add current message
#             messages.append({
#                 "role": "user",
#                 "content": f"[Salesperson]: {current_message}\n\nWho should respond and what should they say?"
#             })
            
#             # Get response from GPT
#             print("🤖 Calling OpenAI API...")
#             response = await client.chat.completions.create(
#                 model=self.model,
#                 messages=messages,
#                 temperature=0.7,
#                 max_tokens=500,
#                 response_format={"type": "json_object"}
#             )
            
#             # Parse response
#             raw_content = response.choices[0].message.content
#             print(f"📝 Raw OpenAI response: {raw_content[:200]}...")
            
#             # ✅ FIXED: Better JSON parsing with error handling
#             try:
#                 result = json.loads(raw_content)
#             except json.JSONDecodeError as e:
#                 print(f"⚠️ JSON parsing error: {e}")
#                 # Try to extract JSON from markdown code blocks
#                 json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_content, re.DOTALL)
#                 if json_match:
#                     result = json.loads(json_match.group(1))
#                 else:
#                     # Fallback response
#                     result = self._create_fallback_response(representatives, current_message)
            
#             # ✅ FIXED: Validate response structure
#             result = self._validate_and_fix_response(result, representatives)
            
#             print(f"✅ Generated response from: {result.get('responding_rep_name')}")
#             return result
            
#         except Exception as e:
#             print(f"❌ OpenAI service error: {e}")
#             import traceback
#             traceback.print_exc()
#             # Return fallback response instead of crashing
#             return self._create_fallback_response(representatives, current_message)
    
#     def _validate_and_fix_response(
#         self, 
#         result: Dict[str, Any], 
#         representatives: List[Dict[str, Any]]
#     ) -> Dict[str, Any]:
#         """Validate and fix AI response structure"""
        
#         # Ensure all required fields exist
#         required_fields = {
#             "responding_rep_id": None,
#             "responding_rep_name": None,
#             "response_text": "I understand. Could you tell me more?",
#             "should_interrupt": False,
#             "interrupting_rep_id": None,
#             "reasoning": "Default response"
#         }
        
#         for field, default_value in required_fields.items():
#             if field not in result or result[field] is None:
#                 # Try to infer from other fields
#                 if field == "responding_rep_id" and not result.get("responding_rep_id"):
#                     # Try to match by name
#                     rep_name = result.get("responding_rep_name")
#                     if rep_name:
#                         for rep in representatives:
#                             if rep.get("name", "").lower() == rep_name.lower():
#                                 result["responding_rep_id"] = rep.get("id")
#                                 break
                    
#                     # Still no ID? Use first rep
#                     if not result.get("responding_rep_id") and representatives:
#                         result["responding_rep_id"] = representatives[0].get("id")
#                         result["responding_rep_name"] = representatives[0].get("name")
                
#                 elif field == "responding_rep_name" and not result.get("responding_rep_name"):
#                     # Try to find by ID
#                     rep_id = result.get("responding_rep_id")
#                     if rep_id:
#                         for rep in representatives:
#                             if rep.get("id") == rep_id:
#                                 result["responding_rep_name"] = rep.get("name")
#                                 break
                    
#                     # Still no name? Use first rep
#                     if not result.get("responding_rep_name") and representatives:
#                         result["responding_rep_name"] = representatives[0].get("name")
                
#                 else:
#                     result[field] = default_value
        
#         # Ensure response_text is not empty
#         if not result.get("response_text") or result["response_text"].strip() == "":
#             result["response_text"] = "That's an interesting point. Let me share my thoughts on that."
        
#         return result
    
#     def _create_fallback_response(
#         self, 
#         representatives: List[Dict[str, Any]], 
#         message: str
#     ) -> Dict[str, Any]:
#         """Create a fallback response when AI fails"""
        
#         if not representatives:
#             return {
#                 "responding_rep_id": "fallback",
#                 "responding_rep_name": "Representative",
#                 "response_text": "I understand. Could you elaborate on that?",
#                 "should_interrupt": False,
#                 "interrupting_rep_id": None,
#                 "reasoning": "Fallback response - AI service unavailable"
#             }
        
#         # Use first representative as fallback
#         first_rep = representatives[0]
        
#         # Generate contextual fallback based on personality
#         personality = first_rep.get("personality_traits", ["neutral"])[0].lower()
        
#         fallback_responses = {
#             "angry": "Look, I don't have time for this. Get to the point.",
#             "arrogant": "I've seen countless pitches like this. What makes yours different?",
#             "soft": "That's interesting. Could you tell me more about that?",
#             "cold_hearted": "What are the numbers? I need concrete data.",
#             "nice": "I appreciate you sharing that. What else should we know?",
#             "analytical": "Can you provide more specific metrics on that?",
#             "neutral": "I see. Could you elaborate further?"
#         }
        
#         response_text = fallback_responses.get(
#             personality, 
#             "That's an interesting point. Please continue."
#         )
        
#         return {
#             "responding_rep_id": first_rep.get("id"),
#             "responding_rep_name": first_rep.get("name"),
#             "response_text": response_text,
#             "should_interrupt": False,
#             "interrupting_rep_id": None,
#             "reasoning": f"Fallback response using {personality} personality"
#         }
    
#     def _build_orchestrator_prompt(
#         self,
#         representatives: List[Dict[str, Any]],
#         salesperson_data: Dict[str, Any],
#         company_data: Dict[str, Any]
#     ) -> str:
#         """Build detailed system prompt for multi-agent orchestration"""
        
#         reps_info = "\n".join([
#             f"""
#             Representative {i+1}:
#             - ID: {rep.get('id', 'unknown')}
#             - Name: {rep.get('name', 'Unknown')}
#             - Role: {rep.get('role', 'Unknown')}
#             - Personality: {', '.join(rep.get('personality_traits', ['neutral']))}
#             - Decision Maker: {rep.get('is_decision_maker', False)}
#             - Tenure: {rep.get('tenure_months', 0)} months
#             - Notes: {rep.get('notes', 'N/A')}
#             """
#             for i, rep in enumerate(representatives)
#         ])
        
#         # Safe extraction of company data
#         company_url = company_data.get('company_url', 'N/A') if company_data else 'N/A'
#         company_info = company_data.get('company_data', {}) if company_data else {}
        
#         prompt = f"""
# You are an AI orchestrator managing a sales meeting simulation with multiple company representatives.

# COMPANY INFORMATION:
# - Company: {company_url}
# - Industry: {company_info.get('industry', 'N/A')}
# - Size: {company_info.get('company_size', 'N/A')}
# - Revenue: {company_info.get('revenue', 'N/A')}

# PRODUCT BEING SOLD:
# - Product: {salesperson_data.get('product_name', 'N/A')}
# - Description: {salesperson_data.get('description', 'N/A')}

# REPRESENTATIVES IN THIS MEETING:
# {reps_info}

# YOUR TASK:
# 1. Analyze the salesperson's message
# 2. Decide which representative should respond based on:
#    - Their role and expertise
#    - Their personality traits
#    - Whether salesperson specifically addressed them
#    - Natural conversation flow
#    - Decision-making authority
# 3. Generate an authentic response that matches the representative's personality
# 4. Determine if another rep might interrupt or add to the conversation

# RESPONSE RULES:
# - If salesperson asks "What do you think, [Name]?" - that specific rep MUST respond
# - If discussing budget/financials - CFO is most likely to respond
# - If discussing technology - CTO is most likely to respond
# - If discussing strategy/vision - CEO is most likely to respond
# - Arrogant personalities will be dismissive, ask tough questions
# - Soft personalities will be encouraging, helpful
# - Cold personalities will be brief, factual, unemotional
# - Decision makers have final say on commitments

# CRITICAL - OUTPUT FORMAT (MUST be valid JSON):
# {{
#     "responding_rep_id": "exact_id_from_representative_list",
#     "responding_rep_name": "exact_name_from_representative_list",
#     "response_text": "The actual response from this representative (2-4 sentences, natural conversation)",
#     "should_interrupt": false,
#     "interrupting_rep_id": null,
#     "reasoning": "Brief explanation of why this rep is responding"
# }}

# IMPORTANT:
# - Keep responses natural and conversational (2-4 sentences)
# - Maintain personality consistency
# - Consider power dynamics and hierarchy
# - Create realistic business meeting interactions
# - ALWAYS use the EXACT id and name from the representatives list above
# - Return ONLY valid JSON, no markdown, no explanations
# """
#         return prompt
    
#     async def generate_top_questions(
#         self,
#         salesperson_data: Dict[str, Any],
#         company_data: Dict[str, Any],
#         meeting_goal: str
#     ) -> List[str]:
#         """Generate top 5 questions salesperson might ask based on context"""
        
#         try:
#             # Safe extraction
#             company_info = company_data.get('company_data', {}) if company_data else {}
            
#             prompt = f"""
# Based on this sales scenario, generate exactly 5 strategic questions the salesperson should ask:

# PRODUCT/SERVICE:
# {salesperson_data.get('product_name', 'Product')} - {salesperson_data.get('description', 'N/A')}

# COMPANY:
# - Industry: {company_info.get('industry', 'N/A')}
# - Size: {company_info.get('company_size', 'N/A')}
# - Current tech: {company_info.get('tech_stack', [])}

# MEETING GOAL:
# {meeting_goal}

# Generate 5 powerful questions that will:
# 1. Uncover pain points
# 2. Qualify the opportunity
# 3. Build rapport
# 4. Advance the sale
# 5. Handle potential objections

# Return ONLY valid JSON with this exact format:
# {{
#     "questions": [
#         "question 1",
#         "question 2", 
#         "question 3",
#         "question 4",
#         "question 5"
#     ]
# }}
# """
            
#             response = await client.chat.completions.create(
#                 model=self.model,
#                 messages=[{"role": "user", "content": prompt}],
#                 temperature=0.8,
#                 response_format={"type": "json_object"}
#             )
            
#             result = json.loads(response.choices[0].message.content)
#             questions = result.get("questions", [])
            
#             # Ensure we have exactly 5 questions
#             if len(questions) < 5:
#                 default_questions = [
#                     "What are your current challenges in this area?",
#                     "How are you handling this currently?",
#                     "What would an ideal solution look like for you?",
#                     "What's your timeline for making a decision?",
#                     "Who else should be involved in this conversation?"
#                 ]
#                 questions.extend(default_questions[len(questions):5])
            
#             return questions[:5]
            
#         except Exception as e:
#             print(f"❌ Error generating questions: {e}")
#             # Return default questions
#             return [
#                 "What are your biggest challenges right now?",
#                 "How does your current solution work?",
#                 "What would success look like for you?",
#                 "What's your timeline for implementation?",
#                 "Who else needs to be part of this decision?"
#             ]


# # Singleton instance
# openai_service = OpenAIService()




from openai import AsyncOpenAI
from app.config.settings import settings
from typing import List, Dict, Any, Optional
import json
import re

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


class OpenAIService:
    """Handle multi-agent conversation using OpenAI GPT"""
    
    def __init__(self):
        self.model = "gpt-4o"
    
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
        Generate response. Returns primary responder + optional secondary.
        
        Returns:
        {
            "primary_rep_id": "...",
            "primary_rep_name": "...",
            "primary_response": "...",
            "secondary_rep_id": null or "...",
            "secondary_rep_name": null or "...",
            "secondary_response": null or "...",
            "reasoning": "..."
        }
        """
        try:
            system_prompt = self._build_orchestrator_prompt(
                representatives, salesperson_data, company_data
            )
            messages = [{"role": "system", "content": system_prompt}]
            
            for turn in conversation_history[-12:]:
                messages.append({
                    "role": "user",
                    "content": f"[{turn['speaker_name']} | id:{turn['speaker']}]: {turn['text']}"
                })
            
            messages.append({
                "role": "user",
                "content": (
                    f"[Salesperson | id:salesperson]: {current_message}\n\n"
                    f"Decide who responds and whether anyone adds to it. Return JSON."
                )
            })
            
            print("🤖 Calling OpenAI API...")
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.8,
                max_tokens=600,
                response_format={"type": "json_object"}
            )
            
            raw_content = response.choices[0].message.content
            print(f"📝 Raw OpenAI response: {raw_content[:300]}...")
            
            try:
                result = json.loads(raw_content)
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parsing error: {e}")
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    result = self._create_fallback_response(representatives, current_message, conversation_history)
            
            result = self._validate_response(result, representatives)
            print(f"✅ Primary: {result.get('primary_rep_name')} | Secondary: {result.get('secondary_rep_name')}")
            return result
            
        except Exception as e:
            print(f"❌ OpenAI service error: {e}")
            import traceback
            traceback.print_exc()
            return self._create_fallback_response(representatives, current_message, conversation_history)
    
    def _validate_response(self, result: Dict[str, Any], representatives: List[Dict[str, Any]]) -> Dict[str, Any]:
        def find_rep(rep_id, rep_name):
            if rep_id:
                for rep in representatives:
                    if rep.get("id") == rep_id or rep.get("_id") == rep_id:
                        return rep
            if rep_name:
                for rep in representatives:
                    if rep.get("name", "").lower() == rep_name.lower():
                        return rep
            return None
        
        primary = find_rep(result.get("primary_rep_id"), result.get("primary_rep_name"))
        if not primary and representatives:
            primary = representatives[0]
        
        if primary:
            result["primary_rep_id"]   = primary.get("id") or str(primary.get("_id"))
            result["primary_rep_name"] = primary.get("name")
        
        if not result.get("primary_response"):
            result["primary_response"] = "That's an interesting point. Could you tell us more?"
        
        secondary = find_rep(result.get("secondary_rep_id"), result.get("secondary_rep_name"))
        if secondary and secondary.get("id") == result.get("primary_rep_id"):
            secondary = None
        
        if secondary and result.get("secondary_response"):
            result["secondary_rep_id"]   = secondary.get("id") or str(secondary.get("_id"))
            result["secondary_rep_name"] = secondary.get("name")
        else:
            result["secondary_rep_id"]   = None
            result["secondary_rep_name"] = None
            result["secondary_response"] = None
        
        if not result.get("reasoning"):
            result["reasoning"] = "Natural conversation flow"
        
        return result
    
    def _get_last_responder_id(self, conversation_history: List[Dict]) -> Optional[str]:
        for turn in reversed(conversation_history):
            if turn.get("speaker") != "salesperson":
                return turn.get("speaker")
        return None
    
    def _create_fallback_response(self, representatives, message, conversation_history=None):
        if not representatives:
            return {
                "primary_rep_id": "fallback", "primary_rep_name": "Representative",
                "primary_response": "I understand. Could you elaborate?",
                "secondary_rep_id": None, "secondary_rep_name": None, "secondary_response": None,
                "reasoning": "Fallback"
            }
        
        last_id = self._get_last_responder_id(conversation_history or [])
        primary = representatives[0]
        if last_id and len(representatives) > 1:
            for rep in representatives:
                if rep.get("id") != last_id:
                    primary = rep
                    break
        
        traits = primary.get("personality_traits", [])
        personality = traits[0].lower() if traits and isinstance(traits[0], str) else "neutral"
        
        fallback_texts = {
            "angry": "Get to the point. What's the value here?",
            "arrogant": "I've heard better pitches. What's actually different?",
            "soft": "That sounds interesting. Could you tell us more?",
            "cold_hearted": "Give me the numbers. That's all I need.",
            "nice": "Thank you for sharing that. What else should we know?",
            "analytical": "Can you provide specific metrics to support that?",
            "neutral": "I see. Could you elaborate further?"
        }
        
        return {
            "primary_rep_id": primary.get("id"), "primary_rep_name": primary.get("name"),
            "primary_response": fallback_texts.get(personality, "That's interesting. Please continue."),
            "secondary_rep_id": None, "secondary_rep_name": None, "secondary_response": None,
            "reasoning": f"Fallback — {personality}"
        }
    
    def _build_orchestrator_prompt(self, representatives, salesperson_data, company_data):
        reps_info = "\n".join([
            f"Rep {i+1}: ID={rep.get('id','?')} | Name={rep.get('name','?')} | Role={rep.get('role','?')} | Personality={','.join(rep.get('personality_traits',['neutral']))} | DecisionMaker={rep.get('is_decision_maker',False)} | Notes={rep.get('notes','N/A')}"
            for i, rep in enumerate(representatives)
        ])
        rep_names    = " and ".join([r.get("name","?") for r in representatives])
        company_url  = company_data.get('company_url', 'N/A') if company_data else 'N/A'
        company_info = company_data.get('company_data', {}) if company_data else {}
        
        return f"""You are managing a realistic sales meeting simulation with: {rep_names}.

COMPANY: {company_url} | Industry: {company_info.get('industry','N/A')} | Size: {company_info.get('company_size','N/A')}
PRODUCT: {salesperson_data.get('product_name','N/A')} — {salesperson_data.get('description','N/A')}
REPS:
{reps_info}

PRIMARY RESPONDER RULES:
- Salesperson mentions a name → that person is PRIMARY (e.g. "what do you think shaikat" → shaikat responds)
- Salesperson says a role (CEO/CFO/CTO) → match by role
- Financial/budget topics → CFO first
- Strategy/vision → CEO first  
- Technical → CTO first
- Otherwise → ROTATE, avoid same person twice in a row
- If LAST message was from rep X → prefer the OTHER rep as primary this time

SECONDARY RESPONDER RULES (optional, ~30% of turns only):
- Only add secondary if it feels genuinely natural
- Must be DIFFERENT person than primary
- Keep secondary to 1-2 sentences max
- Set to null if not natural

PERSONALITY:
angry=hostile/short | arrogant=dismissive | soft=warm | cold_hearted=factual | nice=friendly | analytical=data-focused | neutral=professional

RETURN ONLY THIS JSON (no markdown, no extra text):
{{
    "primary_rep_id": "exact id",
    "primary_rep_name": "exact name",
    "primary_response": "2-4 sentences matching personality",
    "secondary_rep_id": null,
    "secondary_rep_name": null,
    "secondary_response": null,
    "reasoning": "brief reason"
}}"""
    
    async def generate_top_questions(self, salesperson_data, company_data, meeting_goal):
        try:
            company_info = company_data.get('company_data', {}) if company_data else {}
            prompt = f"""Generate 5 strategic sales questions.
PRODUCT: {salesperson_data.get('product_name','?')} — {salesperson_data.get('description','N/A')}
COMPANY: {company_info.get('industry','N/A')} | {company_info.get('company_size','N/A')}
GOAL: {meeting_goal}
Return ONLY: {{"questions": ["q1","q2","q3","q4","q5"]}}"""
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            questions = result.get("questions", [])
            defaults = [
                "What are your current challenges?", "How are you handling this now?",
                "What would an ideal solution look like?", "What's your decision timeline?",
                "Who else needs to be involved?"
            ]
            while len(questions) < 5:
                questions.append(defaults[len(questions)])
            return questions[:5]
        except Exception as e:
            print(f"❌ Error generating questions: {e}")
            return ["What are your biggest challenges?", "How does your current solution work?",
                    "What would success look like?", "What's your implementation timeline?",
                    "Who else needs to be part of this decision?"]

    async def generate_conversation_analytics(
        self,
        conversation_history: List[Dict[str, Any]],
        salesperson_data: Dict[str, Any],
        company_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive post-meeting analytics from the transcript."""
        try:
            # Build transcript string
            transcript = "\n".join([
                f"[{t.get('speaker_name', 'Unknown')}]: {t.get('text', '')}"
                for t in conversation_history
            ])
            
            if not transcript.strip():
                return self._empty_analytics()

            system_prompt = f"""
You are an expert Sales Manager and Conversation Analyst.
Analyze the following sales conversation transcript.

SALESPERSON: {salesperson_data.get('name', 'Unknown')} selling {salesperson_data.get('product_name', 'Product')}
COMPANY: {company_data.get('company_data', {}).get('industry', 'Unknown Industry')}

Your goal is to extract deep insights, MEDDIC criteria, sentiment, and scores.

Return ONLY a valid JSON object matching exactly this structure:
{{
    "overall_score": 85, // 0-100 integer
    "engagement_score": 78, // 0-100 integer representing how engaging the salesperson was
    "summary": "A 2-3 sentence overview of the meeting's key outcomes.", // Concise meeting summary
    "meddic": {{
        "metrics": "...",
        "economic_buyer": "...",
        "decision_criteria": "...",
        "decision_process": "...",
        "identify_pain": "...",
        "champion": "..."
    }},
    "key_points": [
        "Point 1",
        "Point 2"
    ],
    "next_steps": [
        "Step 1"
    ],
    "sentiment": "Positive", // "Positive", "Neutral", "Negative"
    "sentiment_suggestion": "...", // Brief advice based on sentiment
    "active_listening_grade": "A+", // "A+", "A", "A-", "B+", "B", "C", "D"
    "questions_asked": 18, // Total number of questions the salesperson asked
    "open_questions": 14, // Number of open-ended questions the salesperson asked out of the total
    "topics_discussed": [
        "Pricing", "Implementation"
    ],
    "risks": [
        "Risk 1"
    ],
    "opportunities": [
        "Opportunity 1"
    ],
    "ai_insights": {
        "strength": "One specific thing the salesperson did well (1 sentence).",
        "improvement": "One specific area for improvement (1 sentence).",
        "pattern": "A recurring behavior or trend observed in this meeting (1 sentence)."
    }
}}
"""
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"TRANSCRIPT:\n\n{transcript}"}
            ]
            
            print("🤖 Calling OpenAI for comprehensive analytics...")
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3, # low temp for consistent analysis
                response_format={"type": "json_object"}
            )
            
            raw_content = response.choices[0].message.content
            
            try:
                result = json.loads(raw_content)
                return result
            except json.JSONDecodeError:
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                return self._empty_analytics()
                
        except Exception as e:
            print(f"❌ Error generating analytics: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_analytics()

    def _empty_analytics(self) -> Dict[str, Any]:
        return {
            "overall_score": 0,
            "engagement_score": 0,
            "summary": "",
            "meddic": {k: "Not enough data" for k in ["metrics", "economic_buyer", "decision_criteria", "decision_process", "identify_pain", "champion"]},
            "key_points": [], "next_steps": [], "sentiment": "Unknown", "sentiment_suggestion": "No data available to analyze.",
            "active_listening_grade": "N/A", "questions_asked": 0, "open_questions": 0, 
            "topics_discussed": [], "risks": [], "opportunities": [],
            "ai_insights": {
                "strength": "N/A",
                "improvement": "N/A",
                "pattern": "N/A"
            }
        }

    async def generate_account_insights(
        self,
        company_data: Dict[str, Any],
        meetings_summary: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate AI insights for account details page based on all meetings"""
        try:
            meetings_text = ""
            for i, m in enumerate(meetings_summary, 1):
                meetings_text += (
                    f"\nMeeting {i} (id:{m.get('meeting_id','?')}): goal={m.get('meeting_goal', 'N/A')}"
                    f" | Turns: {m.get('total_turns', 0)}"
                    f" | Talk ratio: {m.get('salesperson_talk_ratio', 0)}%"
                    f" | Questions: {m.get('questions_asked', 0)}"
                    f" | Last AI msg: {m.get('last_ai_message', '')[:100]}"
                )

            company_info = company_data.get('company_data', {})
            company_url = company_data.get('company_url', '')

            prompt = f"""You are a sales intelligence AI. Analyze these meetings and return account insights.

COMPANY URL: {company_url}
COMPANY: {company_info.get('industry', 'N/A')} | {company_info.get('company_size', 'N/A')} | Revenue: {company_info.get('revenue', 'N/A')}
MEETINGS ({len(meetings_summary)} total): {meetings_text}

Return ONLY valid JSON:
{{
    "company_name": "<extract from URL or use domain name, e.g. FastGrowth Inc.>",
    "average_engagement_score": <0-100>,
    "engagement_label": "<e.g. Excellent - Highly Engaged>",
    "sentiment_trend": "<improving|declining|stable>",
    "sentiment_trend_label": "<short description>",
    "sentiment_data_points": [
        {{
            "meeting_id": "<id from above>",
            "meeting_goal": "<goal>",
            "sentiment_score": <0-100>,
            "sentiment_label": "<Positive|Neutral|Negative>"
        }}
    ],
    "risk_alerts": [{{"type": "warning|success", "message": "<text>"}}],
    "upsell_opportunities": [{{"title": "<title>", "reason": "<why>"}}],
    "meeting_scores": [
        {{
            "meeting_id": "<id from above>",
            "score": <0-100>,
            "label": "<e.g. Good Performance>"
        }}
    ],
    "opportunities": [
        {{
            "name": "<opportunity name>",
            "value": "<e.g. $125,000>",
            "stage": "<e.g. Negotiation|Discovery|Proposal>",
            "close_date": "<e.g. Mar 15, 2025>",
            "probability": <0-100>
        }}
    ]
}}"""

            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)

        except Exception as e:
            print(f"❌ Error generating account insights: {e}")
            return {
                "company_name": "",
                "average_engagement_score": 0,
                "engagement_label": "No data",
                "sentiment_trend": "stable",
                "sentiment_trend_label": "Not enough data",
                "sentiment_data_points": [],
                "risk_alerts": [],
                "upsell_opportunities": [],
                "meeting_scores": [],
                "opportunities": []
            }

    async def generate_salesperson_insights(
        self,
        salesperson_data: Dict[str, Any],
        meetings_summary: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate high-level coach insights for a salesperson across all meetings"""
        try:
            meetings_text = ""
            for i, m in enumerate(meetings_summary, 1):
                meetings_text += (
                    f"\nMeeting {i}: goal={m.get('meeting_goal', 'N/A')}"
                    f" | Score: {m.get('score', 0)}"
                    f" | Questions: {m.get('questions_asked', 0)}"
                    f" | Open Questions: {m.get('open_questions', 0)}"
                    f" | Engagement: {m.get('engagement_score', 0)}"
                )

            prompt = f"""You are a Sales Coach AI. Analyze these meetings for salesperson {salesperson_data.get('name', 'Unknown')}.
            
PRODUCT: {salesperson_data.get('product_name', 'N/A')}
MEETINGS ({len(meetings_summary)} total): {meetings_text}

Return ONLY valid JSON with exactly these 3 fields:
{{
    "strength": "A powerful 1-sentence observation about what they do well consistently.",
    "improvement": "A 1-sentence actionable area for improvement with specific metrics if possible.",
    "pattern": "A 1-sentence recurring behavior or trend observed across multiple meetings."
}}"""

            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)

        except Exception as e:
            print(f"❌ Error generating salesperson insights: {e}")
            return {
                "strength": "Not enough data yet.",
                "improvement": "Keep practicing more sessions.",
                "pattern": "Analyzing your performance trends."
            }

openai_service = OpenAIService()
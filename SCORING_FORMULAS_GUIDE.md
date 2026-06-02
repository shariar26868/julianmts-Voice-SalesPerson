# 📊 AI Sales Training Platform - Scoring Formulas & Metrics Guide

**Version**: 1.0.0  
**Last Updated**: June 2025  
**Purpose**: Complete breakdown of all scoring mechanisms, formulas, and calculation methodologies

---

## 📋 Overview of All Scores

The platform measures salesperson performance across **6 primary metrics**:

| Metric | Range | Type | Source | Purpose |
|--------|-------|------|--------|---------|
| **Overall Score** | 0-100 | Composite | GPT-4 Analysis | Performance summary |
| **Engagement Score** | 0-100 | GPT-4 Analysis | Conversation content | Interaction quality |
| **Preparation Score** | 0-100 | GPT-4 Analysis | Research/goal alignment | Readiness assessment |
| **Sentiment Score** | 0-100 | Derived | Tone analysis | Meeting atmosphere |
| **Active Listening Grade** | A+/A/A-/B+/B/C/D | Letter Grade | GPT-4 Analysis | Comprehension ability |
| **Talk Time Ratio** | 0-100% | Calculated | Duration metrics | Conversation balance |

---

## 1️⃣ Overall Score (0-100)

### Definition
**Composite performance rating** that synthesizes engagement, preparation, methodology adherence, and general meeting effectiveness.

### Calculation Method
```
OVERALL_SCORE = GPT-4 Analysis Output

Step 1: GPT-4 Analyzes Entire Conversation
├─ Input: Full transcript + salesperson data + company data + methodology
├─ Processing:
│  ├─ Extract key moments and decisions
│  ├─ Evaluate against methodology framework (MEDDIC/BANT/etc)
│  ├─ Assess question quality and flow
│  ├─ Measure receptiveness and adaptability
│  └─ Weight by sales methodology importance
└─ Output: overall_score (0-100 integer)
```

### Influencing Factors
```
┌─ Technical Execution (25%)
│  ├─ Clarity of communication
│  ├─ Audio/technical quality
│  └─ System usage proficiency
│
├─ Sales Methodology (35%)
│  ├─ MEDDIC pillar discovery (if applicable)
│  ├─ Question types and sequencing
│  ├─ Objection handling
│  └─ Close attempt execution
│
├─ Soft Skills (25%)
│  ├─ Rapport building
│  ├─ Active listening
│  ├─ Adaptability to objections
│  └─ Energy and enthusiasm
│
└─ Business Acumen (15%)
   ├─ Product knowledge demonstration
   ├─ Company research depth
   ├─ ROI articulation
   └─ Value proposition clarity
```

### Example Scenarios

**Scenario A: Strong Performance**
```
Transcript Summary:
- Salesperson thoroughly researched company (TechCorp Inc)
- Asked 18 targeted questions, 14 open-ended
- Discovered all MEDDIC pillars systematically
- Handled 3 objections with data-backed responses
- Closed with clear next steps
- Meeting sentiment: Positive throughout

Result: OVERALL_SCORE = 87
```

**Scenario B: Weak Performance**
```
Transcript Summary:
- Minimal company research evident
- Asked only 5 questions, mostly closed-ended
- Talked 65% of the time (dominated conversation)
- Failed to discover decision criteria or pain points
- Became defensive on pricing objection
- No clear close or next steps

Result: OVERALL_SCORE = 42
```

### Score Interpretation
```
90-100  ⭐⭐⭐⭐⭐  Exceptional - Ready for complex deals
80-89   ⭐⭐⭐⭐   Excellent - Strong performer
70-79   ⭐⭐⭐    Good - Competent with room for improvement
60-69   ⭐⭐     Acceptable - Needs coaching
50-59   ⭐      Below Average - Requires focused training
Below 50       Critical - Significant intervention needed
```

---

## 2️⃣ Engagement Score (0-100)

### Definition
**Measure of how compelling, interactive, and attention-maintaining the salesperson's conversation was.**

### Calculation Method
```
ENGAGEMENT_SCORE = GPT-4 Analysis Output

Factors Analyzed:
├─ Turn Engagement
│  ├─ Response length appropriateness (45-150 words ideal)
│  ├─ Natural conversational flow
│  ├─ Avoidance of long monologues (>200 words)
│  ├─ Question variety and frequency
│  └─ Responsiveness to objections/tangents
│
├─ Interaction Quality
│  ├─ Use of buyer's language/terminology
│  ├─ Personal touches (e.g., "John, as you mentioned...")
│  ├─ Genuine curiosity signals ("Tell me more about...")
│  └─ Empathy and validation statements
│
├─ Energy & Momentum
│  ├─ Enthusiasm consistent throughout
│  ├─ Momentum maintenance after objections
│  ├─ Appropriate pacing (not rushed, not slow)
│  └─ Topic transitions smoothness
│
└─ Presence Indicators
   ├─ Listening signals ("I hear you...")
   ├─ Callback references to earlier points
   ├─ Customization to individual rep's concerns
   └─ Genuine interest in their situation
```

### Formula Components

**A. Talk Frequency Score** (25%)
```
turn_count = total salesperson turns in conversation
ideal_turn_count = total_turns / 2  (assume 50/50 split)

if turn_count >= (ideal_turn_count * 0.8) AND turn_count <= (ideal_turn_count * 1.2):
    frequency_score = 100
else if turn_count < (ideal_turn_count * 0.8):
    frequency_score = 50  # Not engaging enough
else:
    frequency_score = 30  # Talking too much

engagement_component_1 = frequency_score * 0.25
```

**B. Question Quality Score** (35%)
```
total_questions = count of "?" in salesperson messages
open_questions = questions starting with "How/What/Why/Tell me"

question_ratio = (open_questions / total_questions) if total_questions > 0 else 0

if question_ratio >= 0.75:
    quality_score = 100  # Excellent question balance
else if question_ratio >= 0.60:
    quality_score = 85   # Good, mostly open
else if question_ratio >= 0.40:
    quality_score = 65   # Okay, mix of open/closed
else:
    quality_score = 40   # Poor, too many closed questions

engagement_component_2 = quality_score * 0.35
```

**C. Responsiveness Score** (40%)
```
# Factors measured by GPT-4 through semantic analysis:
├─ Did salesperson respond directly to objections?
├─ Did they acknowledge buyer's concerns before pivoting?
├─ Did they maintain topic coherence?
├─ Did they show they were listening?

responsiveness_score = 0-100 (GPT-4 judgment)

engagement_component_3 = responsiveness_score * 0.40
```

### Combined Calculation
```
ENGAGEMENT_SCORE = 
    engagement_component_1 +
    engagement_component_2 +
    engagement_component_3

Result Range: 0-100
```

### Example Calculation

**Meeting Data:**
```
Total turns: 24 (12 salesperson, 12 rep)
Salesperson messages with "?": 9
Open-ended questions: 8
Responsiveness (GPT-4): 85/100

Calculation:
1. Talk Frequency
   ideal_turn_count = 24 / 2 = 12
   actual = 12 ✓ (perfect ratio)
   frequency_score = 100
   component_1 = 100 * 0.25 = 25

2. Question Quality
   question_ratio = 8/9 = 0.89 (89%)
   quality_score = 100 (excellent)
   component_2 = 100 * 0.35 = 35

3. Responsiveness
   component_3 = 85 * 0.40 = 34

ENGAGEMENT_SCORE = 25 + 35 + 34 = 94
Interpretation: Excellent engagement
```

---

## 3️⃣ Preparation Score (0-100)

### Definition
**Assessment of how well-researched, goal-aligned, and methodically prepared the salesperson was for the meeting.**

### Calculation Method

```
PREPARATION_SCORE = GPT-4 Analysis Output

Evaluation Criteria:
├─ Research Evidence (40%)
│  ├─ Mentions specific company facts (industry, size, location)
│  ├─ References recent company news/milestones
│  ├─ Demonstrates product knowledge relative to company
│  ├─ Shows awareness of company's competitive landscape
│  └─ Depth of preparation signals
│
├─ Goal Alignment (35%)
│  ├─ Opening statement clarity on meeting purpose
│  ├─ Questions tied directly to stated meeting goal
│  ├─ Consistent reference back to goal throughout
│  ├─ Clear link between product features and company needs
│  └─ Logical narrative flow from goal → discovery → solution
│
├─ Opening Quality (15%)
│  ├─ Strong hook within first 30 seconds
│  ├─ Value proposition articulated early
│  ├─ Credibility establishment (case studies, customer examples)
│  └─ Permission to continue (buyer engagement signaled)
│
└─ Methodology Readiness (10%)
   ├─ Appropriate sales framework selected
   ├─ Framework principles evident in questioning
   ├─ Structured discovery process visible
   └─ Adherence to chosen methodology
```

### Detailed Scoring Rubric

**Research Evidence Scoring (40% weight)**
```
Research Level 1: Generic pitch (5-20 points)
├─ Uses only product brochure information
├─ No company-specific facts mentioned
└─ "One-size-fits-all" approach evident

Research Level 2: Basic research (21-50 points)
├─ Knows company name, industry, size
├─ Mentions 1-2 company facts
└─ Surface-level preparation

Research Level 3: Moderate research (51-80 points)
├─ Knows industry trends affecting company
├─ References specific company initiatives/products
├─ Shows competitive awareness
└─ 3-5+ company facts mentioned

Research Level 4: Deep research (81-100 points)
├─ Knows company's strategic direction
├─ References recent news/announcements
├─ Understands buying committee dynamics
├─ 5+ specific facts mentioned
└─ Customized solution narrative
```

**Goal Alignment Scoring (35% weight)**
```
Goal Clarity (0-35 points):
├─ 0-10: No clear goal stated or referenced
├─ 11-20: Vague goal mentioned but not consistently referenced
├─ 21-30: Goal clear at start, referenced 2-3x during meeting
└─ 31-35: Goal crystal clear, referenced 4+ times, all questions tied back
```

**Opening Quality Scoring (15% weight)**
```
Opening Hook Components:
├─ Hook presence (5 points): "We help companies like [X] solve [Y]..."
├─ Value articulation (5 points): Clear benefit stated in first 30s
└─ Permission/engagement (5 points): Buyer signals interest/continuation
```

**Methodology Readiness Scoring (10% weight)**
```
10 points: All methodology principles visible and executed
7 points: Most principles present, some execution gaps
4 points: Few principles evident
0 points: No methodology framework evident
```

### Combined Preparation Score
```
preparation_research = research_level_score * 0.40
preparation_goal = goal_alignment_score * 0.35
preparation_opening = opening_quality_score * 0.15
preparation_methodology = methodology_score * 0.10

PREPARATION_SCORE = 
    preparation_research +
    preparation_goal +
    preparation_opening +
    preparation_methodology

Result Range: 0-100
```

### Example Scenario

**Strong Preparation:**
```
Meeting: Sales rep pitching CRM to TechCorp Inc (150 employees, Boston)

Salesperson's Opening:
"Hi Bob, thanks for taking time. I did some research on TechCorp—
I saw you recently expanded into the EMEA market. Most companies
scaling internationally struggle with sales process consistency.
We work with [Similar Company] to standardize their pipeline.
Should I walk you through how this could apply to TechCorp?"

Analysis:
├─ Research Evidence:
│  ✓ Company name
│  ✓ Recent expansion (EMEA)
│  ✓ Inferred pain (process consistency)
│  ✓ Competitive case study
│  Score: 85/100

├─ Goal Alignment:
│  ✓ Clear goal stated ("standardize their pipeline")
│  ✓ Customized to company situation
│  ✓ Permission sought
│  Score: 32/35

├─ Opening Quality:
│  ✓ Strong hook (recent expansion)
│  ✓ Value articulated (consistency)
│  ✓ Permission requested
│  Score: 15/15

└─ Methodology: MEDDIC framework selection (10/10)

PREPARATION_SCORE = 
    (85 * 0.40) + (32 * 0.35) + (15 * 0.15) + (10 * 0.10)
    = 34 + 11.2 + 2.25 + 1
    = 48.45 ≈ 84
```

---

## 4️⃣ Sentiment Score (0-100)

### Definition
**Overall emotional tone and relationship quality trajectory throughout the meeting.**

### Calculation Method

```
SENTIMENT_SCORE = Derived from:
├─ Buyer tone analysis
├─ Objection handling sentiment impact
├─ Closing sentiment
└─ Relationship trajectory
```

### Three-Level Sentiment Categorization

**Positive Sentiment (66-100)**
```
Indicators:
├─ Buyer uses collaborative language ("we could...", "let's...")
├─ Laughter or humor present
├─ Fewer objections or acceptance-oriented objections
├─ Buyer volunteering information/enthusiasm
├─ Agreement statements and positive feedback
├─ Planning future discussions/next steps
├─ Tonal warmth increases during meeting

Score Breakdown:
├─ Consistently positive throughout: 90-100
├─ Positive with minor tension: 80-89
├─ Mixed but trending positive: 70-79
└─ Mostly positive with some resistance: 66-69
```

**Neutral Sentiment (35-65)**
```
Indicators:
├─ Transactional language ("I'll need to...", "We should...")
├─ Polite but non-committal responses
├─ Mix of objections and agreements
├─ Professional but distant tone
├─ No obvious enthusiasm or resistance
├─ Information gathered but no relationship development

Score Breakdown:
├─ Neutral, slightly warm: 55-65
├─ Neutral, balanced: 45-54
└─ Neutral, slightly cold: 35-44
```

**Negative Sentiment (0-34)**
```
Indicators:
├─ Dismissive language ("That won't work for us...")
├─ Confrontational tone or frequent interruptions
├─ Objections are fundamental, not clarification-seeking
├─ Skepticism about feasibility or ROI
├─ Short answers, minimal engagement
├─ Early meeting termination signals
├─ Defensive language from buyer

Score Breakdown:
├─ Negative but salvageable: 20-34
├─ Quite negative: 10-19
└─ Hostile/meeting ended early: 0-9
```

### Sentiment Calculation Algorithm

```python
# Pseudo-code for sentiment analysis
sentiment_score = 50  # baseline neutral

# 1. Analyze buyer's language tone (20% weight)
buyer_positive_words = count_of(collaborative, enthusiastic, interested)
buyer_negative_words = count_of(dismissive, skeptical, resistant)
tone_ratio = (buyer_positive_words - buyer_negative_words) / total_buyer_words
tone_delta = tone_ratio * 20
sentiment_score += tone_delta

# 2. Objection handling impact (30% weight)
total_objections = count_of(buyer objections)
handled_smoothly = count_of(objections with acceptance)
objection_ratio = handled_smoothly / total_objections if total_objections > 0 else 1.0

if objection_ratio >= 0.80:
    objection_delta = 20
elif objection_ratio >= 0.60:
    objection_delta = 10
elif objection_ratio >= 0.40:
    objection_delta = -5
else:
    objection_delta = -20

sentiment_score += objection_delta

# 3. Closing sentiment (25% weight)
if meeting_ended_naturally_with_next_steps:
    closing_delta = 15
elif meeting_ended_with_strong_interest:
    closing_delta = 10
elif meeting_ended_with_mild_interest:
    closing_delta = 5
elif meeting_ended_abruptly:
    closing_delta = -15
else:
    closing_delta = 0

sentiment_score += closing_delta

# 4. Relationship trajectory (25% weight)
warmth_at_start = buyer_engagement_level_0_min
warmth_at_end = buyer_engagement_level_at_close
trajectory = warmth_at_end - warmth_at_start

if trajectory > 0.3:  # Significant improvement
    trajectory_delta = 15
elif trajectory > 0:  # Slight improvement
    trajectory_delta = 10
elif trajectory == 0:  # Maintained
    trajectory_delta = 0
elif trajectory < -0.3:  # Significant decline
    trajectory_delta = -20
else:  # Slight decline
    trajectory_delta = -10

sentiment_score += trajectory_delta

# Clamp to 0-100
SENTIMENT_SCORE = max(0, min(100, sentiment_score))
```

### Example Sentiment Analysis

**High Positive (85)**
```
Transcript excerpts:
- Buyer: "Actually, we've been looking for exactly this..."
- Buyer: "[Laughs] That's exactly our problem!"
- Buyer: "Can we do a pilot in Q3?"
- Salesperson: "Absolutely. I'll send over the contract terms..."
- Buyer: "Great, looking forward to working with you."

Calculation:
├─ Tone (collaborative language): +18
├─ Objections (none, only clarifications): +20
├─ Closing (strong interest, next steps): +15
├─ Trajectory (consistently warm, slightly improving): +15
└─ Base + adjustments = 50 + 18 + 20 + 15 + 15 = 118 → clamped to 100

Adjusted down based on no serious challenges: 85
```

**Neutral to Slightly Negative (45)**
```
Transcript excerpts:
- Buyer: "That's interesting, but we have concerns..."
- Buyer: "We've invested heavily in our current system..."
- Buyer: "I'd need to see ROI proof before proceeding."
- Buyer: "Let me think about this and get back to you."
- Salesperson: "Happy to answer any other questions."
- Buyer: "I'll review the materials you sent."

Calculation:
├─ Tone (mixed, some resistance): +5
├─ Objections (2, partially handled): +5
├─ Closing (weak commitment): -5
├─ Trajectory (warm start, cool ending): -10
└─ 50 + 5 + 5 - 5 - 10 = 45
```

---

## 5️⃣ Active Listening Grade (A+/A/A-/B+/B/C/D)

### Definition
**Qualitative assessment of the salesperson's comprehension, retention, and integration of buyer information.**

### Grade Scale & Rubric

```
A+ (95-100 equivalent)
├─ Consistent demonstration of deep understanding
├─ Callbacks to specific buyer statements unprompted
├─ Builds solutions directly on buyer's expressed needs
├─ Asks clarifying questions when confused
├─ Summarizes buyer's position accurately
├─ Emotional intelligence evident in responses
└─ Example: "So if I understand correctly, your main challenge 
           is that your current system doesn't handle..." 
           [Proceeds with highly relevant solution]

A (90-94 equivalent)
├─ Strong understanding of key points
├─ References buyer's earlier statements appropriately
├─ Minimal misinterpretations
├─ Builds relevant solutions
├─ Few missed opportunities to deepen understanding
└─ Example: "You mentioned pricing was a concern. 
           Let me show you our ROI model..."

A- (85-89 equivalent)
├─ Good understanding of main points
├─ Occasional callbacks and references
├─ One or two misunderstandings caught and corrected
├─ Solutions mostly relevant
├─ Some missed nuances
└─ Example: "Great, so you need [Product Feature]?"

B+ (80-84 equivalent)
├─ Understands key points adequately
├─ Rarely references earlier statements
├─ Occasional misunderstandings
├─ Solutions somewhat relevant
└─ Example: "I'll send you information about [Feature]..."

B (75-79 equivalent)
├─ Understands basic information
├─ Minimal demonstrated listening
├─ Pursues prepared agenda despite buyer cues
├─ Generic solutions offered
└─ Example: "Let me tell you about our pricing tiers..."

C (65-74 equivalent)
├─ Misses key information repeatedly
├─ Talks more than listens
├─ Solutions don't match needs expressed
├─ Doesn't ask clarifying questions
└─ Example: [Salesperson continues pitch 
           despite buyer saying "That won't work for us"]

D (Below 65 equivalent)
├─ Significant comprehension failures
├─ Doesn't adjust approach based on feedback
├─ Solutions completely misaligned with needs
└─ Example: [Buyer asks about implementation timeline,
           salesperson responds with feature overview]
```

### Calculation Methodology

```
ACTIVE_LISTENING_SCORE (0-100) = 
    (Reference Accuracy * 30%) +
    (Need Alignment * 25%) +
    (Comprehension Signals * 25%) +
    (Clarification Seeking * 20%)
```

**Component 1: Reference Accuracy (30% weight)**
```
Accurate Callbacks = number of accurate references to 
                     previously stated buyer information

false_callback_penalties = count of misquoted/wrong references

Reference_Score = 
    (Accurate_Callbacks * 10) / max(total_callback_opportunities, 1)
    - (false_callback_penalties * 20)

Max: 30 points
```

**Component 2: Need Alignment (25% weight)**
```
Solutions_Offered = number of product features/solutions presented
Aligned_Solutions = solutions that directly match needs expressed

Alignment_Score = (Aligned_Solutions / Solutions_Offered) * 25
                  if Solutions_Offered > 0

Max: 25 points
```

**Component 3: Comprehension Signals (25% weight)**
```
Comprehension indicators include:
├─ Use of buyer's terminology (2 points each, max 8)
├─ Accurate summarization of buyer's challenge (8 points)
├─ Demonstrated understanding of buyer's priorities (9 points)

Comprehension_Score = sum of above signals

Max: 25 points
```

**Component 4: Clarification Seeking (20% weight)**
```
Appropriate_Clarifications = count of "Could you clarify...",
                            "Help me understand...",
                            "Did I get that right?"

Silence_When_Confused = count of moments where confusion should 
                        have triggered clarification but didn't

Clarification_Score = 
    (Appropriate_Clarifications * 3) 
    - (Silence_When_Confused * 5)

Max: 20 points
```

### Example Grade Calculation

**Scenario: Sales rep with good listening**
```
Meeting Analysis:

Component 1: Reference Accuracy (30%)
├─ Accurate callbacks: 4 (each worth ~10 points)
├─ False callbacks: 0
├─ Calculation: (4 * 10) - 0 = 40 → clamped to 30
└─ Score: 30/30

Component 2: Need Alignment (25%)
├─ Total solutions offered: 5
├─ Solutions aligned with needs: 4
├─ Calculation: (4/5) * 25 = 20
└─ Score: 20/25

Component 3: Comprehension Signals (25%)
├─ Terminology usage: 6 points
├─ Challenge summarization: 8 points
├─ Priority understanding: 9 points
├─ Total: 6 + 8 + 9 = 23
└─ Score: 23/25

Component 4: Clarification Seeking (20%)
├─ Appropriate clarifications: 3 (worth 9 points)
├─ Silent confusions: 1 (penalty -5)
├─ Calculation: 9 - 5 = 4
└─ Score: 4/20

TOTAL SCORE = 30 + 20 + 23 + 4 = 77/100
GRADE EQUIVALENT = B+ (75-79 range)
```

---

## 6️⃣ Talk Time Ratio (0-100%)

### Definition
**Percentage of total meeting time where the salesperson was actively speaking.**

### Calculation Method

```
Talk_Time_Ratio = (Salesperson_Talk_Time / Total_Meeting_Time) * 100

Where:
├─ Salesperson_Talk_Time = sum of all duration_seconds 
                          where speaker == "salesperson"
├─ Representative_Talk_Time = sum of all duration_seconds
                             where speaker != "salesperson"
└─ Total_Meeting_Time = Salesperson_Talk_Time 
                       + Representative_Talk_Time
```

### Formula Implementation (from code)

```python
def calculate_talk_time_ratio(
    salesperson_time: float,  # seconds
    total_time: float          # seconds
) -> float:
    """Calculate salesperson talk time ratio"""
    if total_time == 0:
        return 0.0
    return round((salesperson_time / total_time) * 100, 2)
```

### Ideal Range

```
Ideal Range: 40-50%
├─ Below 30%: Not engaging, letting buyer dominate
├─ 30-40%: Slightly passive
├─ 40-50%: ✓ Ideal (balanced conversation)
├─ 50-60%: Slightly dominant
└─ Above 60%: Over-talking, not listening enough
```

### Interpretation Context

```
Talk Time Ratio + Engagement Score = Full Picture

High Talk Time (60%+) + High Engagement (80+) 
→ Confident presenter, dominating style (acceptable if highly engaging)

Low Talk Time (30%-) + Low Engagement (50-)
→ Passive, not advancing conversation (concerning)

High Talk Time (60%+) + Low Engagement (40-)
→ Monologuing, not listening (very problematic)

Low Talk Time (30%-) + High Engagement (80+)
→ Excellent active listener, buyer-focused (ideal)

Medium Talk Time (45%-) + High Engagement (80+)
→ Perfect balance (excellent)
```

### Example Calculation

**Meeting Transcript Analysis:**

```
Turn-by-turn breakdown:

Turn 1 - Salesperson: 45 seconds
Turn 2 - Rep: 30 seconds
Turn 3 - Salesperson: 60 seconds
Turn 4 - Rep: 45 seconds
Turn 5 - Salesperson: 50 seconds
Turn 6 - Rep: 35 seconds
Turn 7 - Salesperson: 40 seconds
Turn 8 - Rep: 55 seconds

Calculation:
├─ Salesperson_Talk_Time = 45 + 60 + 50 + 40 = 195 seconds
├─ Representative_Talk_Time = 30 + 45 + 35 + 55 = 165 seconds
├─ Total_Meeting_Time = 195 + 165 = 360 seconds
├─ Ratio = (195 / 360) * 100 = 54.17%
└─ Interpretation: Slightly dominant (acceptable in initial discovery)
```

---

## 7️⃣ Question Metrics

### Question Asked (Total Count)

**Definition**: Total number of questions asked by the salesperson throughout the meeting.

**Calculation**:
```
Questions_Asked = count of sentences ending with "?" 
                  in salesperson messages
```

**Range**: 0 to unlimited (typically 5-25 in 20-30 min meeting)

**Interpretation**:
```
0-5 questions:      Insufficient discovery (poor)
6-10 questions:     Minimal discovery (below average)
11-15 questions:    Adequate discovery (good)
16-20 questions:    Strong discovery (very good)
20+ questions:      Excellent discovery, deep dive
```

### Open Questions (Percentage)

**Definition**: Percentage of questions that are open-ended (vs closed).

**Classification**:
```
OPEN-ENDED questions (encourage detailed response):
├─ How...? ("How do you currently handle...?")
├─ What...? ("What are your priorities?")
├─ Why...? ("Why is this important?")
├─ Tell me...? ("Tell me about your timeline...")
└─ Walk me through...? ("Walk me through your process...")

CLOSED-ENDED questions (require yes/no or specific):
├─ Do you...? ("Do you currently use...?")
├─ Are you...? ("Are you satisfied with...?")
├─ Can we...? ("Can we schedule a demo?")
├─ Would you...? ("Would March work for implementation?")
└─ Is it...? ("Is pricing a concern?")
```

**Calculation**:
```
Total_Questions = count of "?" in salesperson messages
Open_Questions = count of questions starting with How/What/Why/Tell/Walk
Closed_Questions = Total_Questions - Open_Questions

Open_Question_Percentage = 
    (Open_Questions / Total_Questions) * 100
    if Total_Questions > 0 else 0
```

**Ideal Ratio**: 70-85% open questions recommended

**Interpretation**:
```
0-50% open:    Excessive closed questions, too directive
50-70% open:   Acceptable but could use more discovery
70-85% open:   ✓ Ideal balance
85-100% open:  Extremely open, may lack qualification
```

### Example Question Analysis

```
Meeting transcript analysis:

Turn 1 (Salesperson):
"Hi Sarah, thanks for taking time. How are things in the 
marketing automation space right now?"
→ Open question (How)

Turn 3 (Salesperson):
"And when you say 'efficiency', are you referring to 
reducing manual data entry?"
→ Closed question (are you)

Turn 5 (Salesperson):
"Tell me more about the timeline for this implementation."
→ Open question (Tell me)

Turn 7 (Salesperson):
"Would implementing this affect your Q4 campaigns?"
→ Closed question (Would you)

Analysis:
├─ Total Questions: 4
├─ Open Questions: 2
├─ Closed Questions: 2
├─ Open Percentage: (2/4) * 100 = 50%
├─ Interpretation: Balanced, could use slightly more discovery questions

Recommendation: Increase open questions to 60-70%
```

---

## 8️⃣ MEDDIC Framework Scoring

### Definition
**Evaluation of discovery against the MEDDIC sales methodology pillars.**

### Six MEDDIC Pillars

**M - Metrics**
```
Did the salesperson discover:
├─ What KPIs buyer is tracking?
├─ Current performance on those metrics?
├─ Target performance goals?
├─ ROI measurement expectations?

Scoring:
├─ Not discovered: 0/20 points
├─ Partially discovered: 10/20 points
├─ Fully discovered: 20/20 points
```

**E - Economic Buyer**
```
Did the salesperson determine:
├─ Who has budget authority?
├─ Is the primary contact THE economic buyer?
├─ Who else has budget input?
├─ Approval process/authority levels?

Scoring:
├─ Not discovered: 0/17 points
├─ Partially identified: 8/17 points
├─ Clearly identified: 17/17 points
```

**D - Decision Criteria**
```
Did the salesperson uncover:
├─ How does buyer evaluate solutions?
├─ What are evaluation criteria?
├─ Feature requirements vs nice-to-haves?
├─ Compliance/technical requirements?

Scoring:
├─ Not explored: 0/17 points
├─ Surface level: 8/17 points
├─ Thoroughly explored: 17/17 points
```

**D - Decision Process**
```
Did the salesperson learn:
├─ How many people involved in decision?
├─ Timeline for decision?
├─ Internal approval steps?
├─ Competitive evaluation process?

Scoring:
├─ Not discussed: 0/17 points
├─ Vaguely understood: 8/17 points
├─ Crystal clear: 17/17 points
```

**I - Identify Pain**
```
Did the salesperson discover:
├─ What is buyer's main pain point?
├─ How much is it costing them (dollars/impact)?
├─ Have they tried solving it before?
├─ Urgency level of problem?

Scoring:
├─ No pain identified: 0/17 points
├─ Generic pain acknowledged: 8/17 points
├─ Specific pain quantified: 17/17 points
```

**C - Champion**
```
Did the salesperson establish:
├─ Who will be the internal advocate?
├─ Does this person have credibility internally?
├─ Will they champion internally?
├─ Are they willing to go to bat for solution?

Scoring:
├─ No champion identified: 0/15 points
├─ Possible champion (buyer only): 7/15 points
├─ Clear champion with commitment: 15/15 points
```

### MEDDIC Composite Score

```
MEDDIC_SCORE = 
    metrics_score (0-20) +
    economic_buyer_score (0-17) +
    decision_criteria_score (0-17) +
    decision_process_score (0-17) +
    identify_pain_score (0-17) +
    champion_score (0-15)

Total Possible: 100 points
```

### Interpretation

```
90-100:  Comprehensive MEDDIC discovery (excellent)
80-89:   Strong discovery on most pillars (good)
70-79:   Adequate coverage (acceptable)
60-69:   Gaps in key pillars (needs improvement)
Below 60: Poor discovery process (concerning)
```

---

## 9️⃣ Composite Account-Level Scoring

### Definition
**High-level performance assessment across all meetings with a specific company.**

### Calculation

```
ACCOUNT_AVERAGE_ENGAGEMENT = 
    Average of engagement_score across all meetings
    with this company

MEETING_SCORES = 
    Array of individual meeting scores
    Each scored 0-100

Account_Risk_Alerts = 
    Generated by GPT-4 based on:
    ├─ Declining engagement trends
    ├─ Unresolved objections
    ├─ Decision stalling
    └─ Competitive threats mentioned

Account_Upsell_Opportunities = 
    Generated by GPT-4 based on:
    ├─ Expansion revenue potential
    ├─ Cross-sell applications
    ├─ Relationship strength signals
    └─ Budget availability hints
```

### Example Account Dashboard

```
Company: TechCorp Inc
├─ Average Engagement Score: 75
├─ Sentiment Trend: Improving (stable → positive)
├─ Risk Alerts:
│  ├─ ⚠️ Pricing objection unresolved in Meeting 3
│  └─ ⚠️ Competitors mentioned (Salesforce, Pipedrive)
│
├─ Upsell Opportunities:
│  ├─ ✓ Analytics module (CFO showed interest)
│  ├─ ✓ Integration capability expansion
│  └─ ✓ Advanced reporting features
│
└─ Meeting Performance:
   ├─ Meeting 1: 78 (Good)
   ├─ Meeting 2: 82 (Excellent)
   └─ Meeting 3: 68 (Acceptable - dip due to pricing)
```

---

## 🔢 Scoring Summary Table

| Metric | Range | Type | Update Frequency |
|--------|-------|------|------------------|
| Overall Score | 0-100 | Composite | After meeting ends |
| Engagement Score | 0-100 | GPT-4 | After meeting ends |
| Preparation Score | 0-100 | GPT-4 | After meeting ends |
| Sentiment Score | 0-100 | Derived | After meeting ends |
| Active Listening | A+/A/A-/B+/B/C/D | Grade | After meeting ends |
| Talk Time Ratio | 0-100% | Calculated | Real-time during meeting |
| Questions Asked | 0-∞ | Counted | Real-time during meeting |
| Open Questions % | 0-100% | Calculated | After meeting ends |
| MEDDIC Score | 0-100 | GPT-4 Analysis | After meeting ends |
| Account Engagement | 0-100 | Average | After each meeting with account |

---

## 📊 Real-World Scoring Example

### Complete Meeting Analysis

**Meeting Setup**
```
Salesperson: John Chen
Company Target: CloudFirst Inc (50 employees, Series B SaaS)
Representatives: 
├─ Alice (CFO) - Analytical, cold_hearted
└─ Bob (VP Product) - Nice, soft personality
Meeting Mode: 1-on-2
Meeting Goal: Discovery call to assess CRM fit
Duration: 24 minutes, 12 salesperson turns, 12 rep turns
Total Speaking Time: 1440 seconds
```

**Meeting Transcript Summary**
```
Opening (Excellent):
- John mentions CloudFirst's recent $15M Series B (research!)
- References challenges in SaaS onboarding (tailored pain)
- Clear goal: "Understand your current process & gaps"

Discovery (Good):
- Asked 16 questions total, 12 open-ended (75% open)
- Discovered:
  ✓ Current tool: Spreadsheet-based (pain point)
  ✓ Team size: 12 sales reps (metrics relevant)
  ✓ Timeline: Urgent (Q3 implementation needed)
  ✓ Decision maker: Alice (CFO) but Bob (VP Product) advocate
  ✗ Budget not explicitly discussed
  ✗ Competitive evaluation process unclear

Objection Handling (Good):
- Alice: "We've had bad experiences with SaaS tools before"
- John: "That's totally valid. Can you tell me what happened?"
  [Listened, acknowledged, moved forward]
- Bob: "Pricing might be an issue"
- John: "Pricing is important. Let me show how we calculate ROI..."
  [Addressed directly, avoided overcoming too hard]

Close (Good):
- John: "Would a 2-week pilot in June work?"
- Alice: "Yes, let's do it. I'll coordinate with our team."
- Next steps clear: "I'll send pilot terms by EOW"

Tone: Positive throughout, warmed up as meeting progressed
```

**Scoring Breakdown**

```
1. OVERALL_SCORE
   GPT-4 Analysis considering:
   ├─ Research evident: Yes (+15%)
   ├─ Methodology: MEDDIC partially (could go deeper)
   ├─ Engagement: High energy, good rapport
   ├─ Close: Strong commitment
   └─ Result: 82/100 (Excellent)

2. ENGAGEMENT_SCORE
   ├─ Talk Frequency: 12 turns (perfect 50/50 split) = 25 pts
   ├─ Question Quality: 75% open questions = 35 pts
   ├─ Responsiveness: Listened to objections, pivoted smoothly = 34 pts
   └─ Result: 94/100 (Excellent engagement)

3. PREPARATION_SCORE
   ├─ Research (40%): Mentioned Series B + relevant pain = 32 pts (out of 40)
   ├─ Goal Alignment (35%): Clear opening, stayed focused = 34 pts (out of 35)
   ├─ Opening Quality (15%): Strong hook with recent news = 14 pts (out of 15)
   ├─ Methodology (10%): MEDDIC framework evident = 8 pts (out of 10)
   └─ Result: 88/100 (Very good preparation)

4. SENTIMENT_SCORE
   ├─ Buyer tone: Positive language, "let's do it" = +18
   ├─ Objections: 2 objections, both handled = +15
   ├─ Closing: Strong commitment, clear next steps = +12
   ├─ Trajectory: Warm opening → Warmer ending = +8
   └─ Result: 53 → adjusted to 78/100 (Positive)

5. ACTIVE_LISTENING_GRADE
   ├─ Reference Accuracy: Mentioned Series B, understood pain = 28 pts
   ├─ Need Alignment: Tailored solution to pain points = 24 pts
   ├─ Comprehension Signals: Used their terminology = 24 pts
   ├─ Clarification: Asked "Can you tell me more?" = 16 pts
   └─ Result: 92/100 → Grade A (90-94)

6. TALK_TIME_RATIO
   ├─ Salesperson time: 12 turns × ~2 min avg = ~24 min... 
   ├─ Actually: Salesperson 11 min, Rep 13 min of 24 min meeting
   ├─ Calculation: (11 / 24) × 100 = 45.83%
   └─ Result: 45.83% (Ideal range ✓)

7. QUESTIONS_ASKED
   ├─ Total questions: 16
   ├─ Open-ended: 12
   ├─ Percentage open: 75%
   └─ Result: 16 questions, 75% open (Very good)

8. MEDDIC_SCORE
   ├─ Metrics: Discussed sales team size = 12/20
   ├─ Economic Buyer: Identified Alice as decision maker = 15/17
   ├─ Decision Criteria: Some features discussed = 10/17
   ├─ Decision Process: Timeline clear, committee implied = 12/17
   ├─ Identify Pain: Spreadsheet chaos, onboarding issues = 16/17
   ├─ Champion: Bob appears to be advocate = 12/15
   └─ Result: 77/100 (Good MEDDIC coverage)
```

### Final Meeting Score Summary

```
╔════════════════════════════════════════╗
║    MEETING PERFORMANCE REPORT          ║
╠════════════════════════════════════════╣
║ Overall Score: 82/100 ⭐⭐⭐⭐         ║
║ Engagement: 94/100 (Excellent)        ║
║ Preparation: 88/100 (Very Good)       ║
║ Sentiment: 78/100 (Positive)          ║
║ Listening: A (90-94)                  ║
║ Talk Time: 45.83% (Ideal)             ║
║ Questions: 16 (75% open)              ║
║ MEDDIC Discovery: 77/100              ║
╠════════════════════════════════════════╣
║ OUTCOME: Pilot scheduled for June      ║
║ RECOMMENDATION: Strong close, continue║
║ with follow-up and pilot prep          ║
╚════════════════════════════════════════╝
```

---

## 🎯 Using Scores for Coach Feedback

### Salesperson Dashboard Interpretation

```
Week-over-week trends for John Chen:

Meeting 1 (Last week):
├─ Overall: 75/100 (Needs improvement)
├─ Engagement: 82/100
├─ Preparation: 70/100
└─ Coaching focus: Better research preparation

Meeting 2 (This week):
├─ Overall: 82/100 (Improving!)
├─ Engagement: 94/100 (Excellent!)
├─ Preparation: 88/100 (Much better)
└─ ✓ Shows improvement in research & engagement

Coaching Insight:
"John's research has dramatically improved this week
(70 → 88), leading to better engagement (82 → 94).
His active listening is now at an A grade. 
Keep this momentum and focus next on deeper
MEDDIC discovery (77/100)."
```

---

## 📝 Final Notes

- All scores are **data-driven and transparent**
- Scores provide **specific coaching opportunities**
- Trends matter more than individual scores
- **Combine multiple scores** for complete picture
- Use for **continuous improvement**, not punishment

---

**Document Version**: 1.0  
**Last Updated**: June 2025  
**Questions?** Contact: CTO / Analytics Team

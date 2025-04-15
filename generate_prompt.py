"""
Prompt generation utilities for RFP response generation
"""
import json
import logging
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_rfp_prompt(requirement: str, category: Optional[str] = None, previous_responses: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """
    Create an optimized prompt for RFP response generation.

    Args:
        requirement: The current RFP requirement to address.
        category: Functional category of the requirement (optional).
        previous_responses: List of previous responses with their similarity scores (optional).

    Returns:
        List of message dictionaries for LLM.
    """
    logger.info(f"Creating prompt for requirement: {requirement}")
    logger.info(f"Category: {category}")
    logger.info(f"Previous responses available: {len(previous_responses or [])} items")
    
    # Create the system message with detailed instructions
    system_message = {
        "role": "system",
        "content": f"""You are a senior RFP specialist with over 15 years of experience in wealth management software.
Your expertise lies in crafting precise, impactful, and business-aligned responses to RFP requirements.

**CONTEXT**:
- Domain: Wealth Management Software.
- Requirement Category: {category or 'Financial Technology'}.
- Current Requirement: {requirement}.
- Audience: Business professionals and wealth management decision-makers.

**TASK**:
Develop a high-quality response to the current RFP requirement. Use the provided previous responses as source material, prioritizing content from responses with higher similarity scores.

**GUIDELINES**:
1. **Response Style**:
   - Professional, clear, and concise.
   - Accessible to business professionals, avoiding excessive technical jargon.
   - Focus on business benefits, practical applications, and value propositions.
   - Ensure the response is complete and submission-ready.

2. **Content Rules**:
   - Incorporate content from the provided previous responses where relevant.
   - Prioritize responses with higher similarity scores for relevance.
   - Include technical details only when needed to demonstrate capability.
   - Maintain an appropriate length (200-400 words) based on the complexity of the requirement.

3. **Response Structure**:
   - **Opening Statement**: Highlight the most relevant feature or capability related to the requirement.
   - **Supporting Information**: Include specific examples or benefits that reinforce the feature.
   - **Value Proposition**: End with a strong, tailored statement of value.

4. **Critical Constraints**:
   - Do NOT include any meta-text or commentary (e.g., "Here's the response…", 'Draft Response').
   - Do NOT include speculative or ambiguous language.
   - Format your response as direct informational content, not as a letter with salutation and signature.
"""
    }
    
    # Format the previous responses for the prompt
    formatted_examples = ""
    if previous_responses and len(previous_responses) > 0:
        for i, resp in enumerate(previous_responses[:3], 1):  # Use up to 3 similar responses
            score = resp.get('similarity_score', 0)
            if isinstance(score, str):
                try:
                    score = float(score)
                except:
                    score = 0
                    
            formatted_examples += f"**Example {i} (Similarity: {score:.2f})**:\n"
            formatted_examples += f"Requirement: {resp.get('requirement', '')}\n"
            formatted_examples += f"Response: {resp.get('response', '')}\n\n"
    
    # Create user message with requirement and examples
    user_message = {
        "role": "user",
        "content": f"""You have the following previous responses with similarity scores to evaluate:

**Previous Responses and Scores**:
{formatted_examples or "No previous responses available. Create an original response based on your expertise."}

**Instructions**:
1. Analyze the responses, prioritizing those with higher scores for relevance.
2. Draft a response that meets all guidelines and rules outlined in the system message.
3. Ensure the response is clear, concise, and tailored to the given requirement.

**Current Requirement**: {requirement}
"""
    }
    
    # Add validation message as a final check
    validation_message = {
        "role": "user",
        "content": """Review and validate the draft response based on these criteria:
1. Content is appropriate and relevant to the requirement.
2. The tone is professional and business-focused.
3. No meta-text, assumptions, or speculative language is present.
4. No salutation like "Dear [Client's Name]" or signature block is included.
5. The response delivers a clear, specific value proposition for the requirement.

If any criteria are unmet, revise the response accordingly."""
    }
    
    # Create the full message array
    messages = [system_message, user_message, validation_message]
    
    # Print the full prompt for debugging
    prompt_preview = f"""
======== GENERATED PROMPT ========
SYSTEM: {system_message['content'][:200]}...
USER: {user_message['content'][:200]}...
VALIDATION: {validation_message['content'][:200]}...
================================
"""
    print(prompt_preview)
    logger.info(prompt_preview)
    
    return messages

def convert_prompt_to_claude(prompt: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert a standard prompt format to Claude-compatible format.

    Args:
        prompt: List of message dictionaries in standard format.

    Returns:
        List of message dictionaries in Claude format.
    """
    claude_messages = []
    system_message = ""

    # Extract system message if present
    for msg in prompt:
        if msg['role'] == 'system':
            system_message = msg['content']
            break

    # Convert messages
    for msg in prompt:
        if msg['role'] == 'system':
            continue  # Skip system messages as they're handled differently

        if msg['role'] == 'assistant':
            claude_messages.append({
                'role': 'assistant',
                'content': msg['content']
            })
        elif msg['role'] == 'user':
            # If there's a system message and this is the first user message,
            # prepend it to the content
            if system_message and not claude_messages:
                content = f"{system_message}\n\nHuman: {msg['content']}"
                claude_messages.append({
                    'role': 'user',
                    'content': content
                })
            else:
                claude_messages.append({
                    'role': 'user',
                    'content': msg['content']
                })

    return claude_messages

def find_similar_matches_and_generate_prompt(requirement_id: int) -> List[Dict[str, Any]]:
    """
    Find similar matches for a requirement and use them to generate a prompt.

    Args:
        requirement_id: ID of the requirement to find matches for

    Returns:
        List of message dictionaries for the LLM
    """
    try:
        # Import here to avoid circular imports
        from find_matches import find_similar_matches
        from database import engine
        from sqlalchemy import text
        
        # Get the requirement details
        with engine.connect() as connection:
            req_query = text("""
                SELECT id, requirement, category 
                FROM excel_requirement_responses 
                WHERE id = :req_id
            """)
            requirement = connection.execute(req_query, {"req_id": requirement_id}).fetchone()
            
            if not requirement:
                logger.error(f"No requirement found with ID: {requirement_id}")
                return create_rfp_prompt(f"Missing requirement with ID {requirement_id}")
        
        # Find similar matches
        matches_result = find_similar_matches(requirement_id)
        
        if not matches_result.get("success", False):
            logger.error(f"Error finding similar matches: {matches_result.get('error', 'Unknown error')}")
            return create_rfp_prompt(requirement[1], requirement[2])
        
        # Extract similar matches
        similar_matches = matches_result.get("similar_matches", [])
        
        # Create the prompt using the requirement and similar matches
        return create_rfp_prompt(requirement[1], requirement[2], similar_matches)
        
    except Exception as e:
        logger.error(f"Error in find_similar_matches_and_generate_prompt: {str(e)}")
        return create_rfp_prompt("Error retrieving requirement information")
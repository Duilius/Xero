from app.core.prompts.classifier_prompt import CLASSIFIER_PROMPT

async def process_general_query(query_text: str, llm_model=None):
    """Procesa consultas generales usando el modelo LLM"""
    try:
        response = await llm_model.generate(
            prompt=CLASSIFIER_PROMPT,
            user_input=query_text
        )
        return {
            "response": response,
            "type": "general_query"
        }
    except Exception as e:
        raise Exception(f"Error processing general query: {str(e)}")
from app.core.prompts.classifier_prompt import CLASSIFIER_PROMPT
import json

class QueryClassifier:
    def __init__(self, llm_model):
        self.llm = llm_model
        self.prompt = CLASSIFIER_PROMPT

    async def classify_query(self, user_query: str) -> dict:
        response = await self.llm.generate(
            prompt=self.prompt,
            user_query=user_query
        )
        return json.loads(response)
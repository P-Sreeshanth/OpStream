import os
from huggingface_hub import InferenceClient

class PatchGenerator:
    def __init__(self):
        self.api_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
        if not self.api_token:
            raise ValueError("HUGGINGFACEHUB_API_TOKEN is required")
            
        self.client = InferenceClient(token=self.api_token)
        # Use a model that works well with text_generation API
        self.model = "mistralai/Mistral-7B-Instruct-v0.2"

    def generate_patch(self, issue_description: str, file_content: str) -> str:
        """
        Generates a fixed version of the file content based on the issue description.
        """
        # Format prompt for Mistral instruct model
        prompt = f"""<s>[INST] You are an expert open source contributor.
Your task is to fix a bug or add a feature in a file based on an issue description.

RULES:
1. You must output the FULL content of the fixed file.
2. Do NOT wrap your output in markdown code blocks.
3. Keep changes minimal and focused on the issue.
4. Ensure the code is valid and syntactically correct.

Issue Description:
{issue_description}

Original File Content:
{file_content}

Output the complete fixed file content: [/INST]"""

        try:
            # Use text_generation which is available in huggingface_hub 0.20.1
            result = self.client.text_generation(
                prompt,
                model=self.model,
                max_new_tokens=2048,
                temperature=0.1,
                top_p=0.9,
                do_sample=True
            )
            
            # Clean up result if wrapped in markdown code blocks
            cleaned_result = result.strip()
            
            # Remove various code block formats
            for lang in ['python', 'javascript', 'typescript', 'js', 'ts', 'jsx', 'tsx', 'vue', 'markdown', 'md', 'sql', 'svelte', 'css', '']:
                block_start = f"```{lang}"
                if cleaned_result.startswith(block_start):
                    cleaned_result = cleaned_result[len(block_start):].lstrip()
                    break
            
            if cleaned_result.endswith("```"):
                cleaned_result = cleaned_result[:-3].rstrip()
                
            return cleaned_result.strip()

        except Exception as e:
            raise ValueError(f"AI Generation failed: {e}")

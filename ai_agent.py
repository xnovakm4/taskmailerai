# ai_agent.py

import requests
import logging
from openai import OpenAI, AzureOpenAI

class AIAgent:
    def __init__(self, config):
        # Initialize OpenRouter if enabled
        openrouter_config = config.get('openrouter', {})
        self.openrouter_enabled = openrouter_config.get('enabled', False)
        self.openrouter_api_key = openrouter_config.get('api_key', '')
        self.openrouter_default_model = openrouter_config.get('default_model', 'openai/gpt-4o-mini')

        # Initialize OpenAI if enabled
        openai_config = config.get('openai', {})
        self.openai_enabled = openai_config.get('enabled', False)
        self.openai_api_key = openai_config.get('api_key', '')
        self.openai_default_model = openai_config.get('default_model', 'gpt-4o-mini')
        if self.openai_enabled and self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None
        
        # Initialize Ollama if enabled
        ollama_config = config.get('ollama', {})
        self.ollama_enabled = ollama_config.get('enabled', False)
        self.ollama_host = ollama_config.get('host', 'http://localhost:11434')
        self.ollama_default_model = ollama_config.get('default_model', 'deepseek-coder:8b')
        
        # Initialize Azure OpenAI if enabled
        azure_config = config.get('azure_openai', {})
        self.azure_enabled = azure_config.get('enabled', False)
        if self.azure_enabled and azure_config.get('api_key') and azure_config.get('endpoint'):
            self.azure_client = AzureOpenAI(
                api_key=azure_config['api_key'],
                api_version=azure_config['api_version'],
                azure_endpoint=azure_config['endpoint']
            )
            self.azure_deployment = azure_config.get('default_model', 'gpt-4o-mini')
        else:
            self.azure_client = None
    
    def call_openrouter_api(self, prompt, model):
        if not self.openrouter_enabled:
            logging.error("OpenRouter interface is disabled")
            return None
            
        # URL a hlavičky pro OpenRouter API
        url = 'https://openrouter.ai/api/v1/chat/completions'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.openrouter_api_key}',
            'HTTP-Referer': 'your-email@example.com',
            'X-Title': 'My Application',
            'X-Subtitle': 'Email AI Assistant',
        }
        if not model:
            model = self.openrouter_default_model
        # Tělo požadavku
        data = {
            'model': model,
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.8
        }

        logging.warning(f"Posilam dotaz do Openrouter API ({model}): {data}")
        response = requests.post(url, headers=headers, json=data)
                                
        if response.status_code == 200:
            json_response = response.json()
            ai_reply = json_response['choices'][0]['message']['content']
            logging.warning(f"Odpoved od API: {ai_reply}")
            return ai_reply
        else:
            logging.error("Chyba při volání OpenRouter API:", response.status_code, response.text)
            return None
            
    def call_ollama_api(self, prompt, model=None):
        """
        Method for communicating with local Ollama API
        """
        if not self.ollama_enabled:
            logging.error("Ollama interface is disabled")
            return None
            
        if not model:
            model = self.ollama_default_model
            
        url = f"{self.ollama_host}/api/generate"
        headers = {'Content-Type': 'application/json'}
        data = {
            'model': model,
            'prompt': prompt,
            'stream': False
        }
        
        logging.warning(f"Sending request to Ollama API ({model}): {prompt}")
        
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                ai_reply = response.json()['response']
                logging.warning(f"Response from Ollama API: {ai_reply}")
                return ai_reply
            else:
                logging.error(f"Error calling Ollama API: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logging.error(f"Error calling Ollama API: {str(e)}")
            return None

    def call_openai_api(self, prompt, model):
        """
        Metoda pro komunikaci s OpenAI API využívající oficiální knihovnu
        """
        if not self.openai_enabled or not self.openai_client:
            logging.error("OpenAI interface is disabled or not configured")
            return None
            
        if not model:
            model = self.openai_default_model
        logging.warning(f"Posílám dotaz do OpenAI API ({model}): {prompt}")
        
        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=1
            )
            
            ai_reply = response.choices[0].message.content
            logging.warning(f"Odpověď od OpenAI API: {ai_reply}")
            return ai_reply
            
        except Exception as e:
            logging.error(f"Chyba při volání OpenAI API: {str(e)}")
            return None

    def call_azure_openai_api(self, prompt, model=None):
        """
        Metoda pro komunikaci s Azure OpenAI API
        """
        if not self.azure_enabled:
            logging.error("Azure OpenAI interface is disabled")
            return None
        if not self.azure_client:
            logging.error("Azure OpenAI není nakonfigurován")
            return None

        if not model:
            model = self.azure_deployment  # Use deployment name as default model

        logging.warning(f"Posílám dotaz do Azure OpenAI API ({model}): {prompt}")
        
        try:
            response = self.azure_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=1
)
            
            ai_reply = response.choices[0].message.content
            logging.warning(f"Odpověď od Azure OpenAI API: {ai_reply}")
            return ai_reply
            
        except Exception as e:
            logging.error(f"Chyba při volání Azure OpenAI API: {str(e)}")
            return None

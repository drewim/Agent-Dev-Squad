import json
import requests
import logging
from typing import Dict, Any, Type, Generator
from pydantic import BaseModel, ValidationError

class OllamaClient:
    """
    A client for interacting with the Ollama API.
    """
    def __init__(self, host='http://localhost:11434', logger=None):
        self.host = host
        if logger:
             self.logger = logger
        else:
             self.logger = logging.getLogger("ollama_client")
             self.logger.setLevel(logging.DEBUG)
             ch = logging.StreamHandler()
             formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
             ch.setFormatter(formatter)
             self.logger.addHandler(ch)

    def generate_text(self, model: str, prompt: str, system_prompt: str = None, stream: bool = False, response_model: Type[BaseModel] = None) -> str | BaseModel | None:
        """
        Generates text using the Ollama API.

        Args:
            model (str): The name of the model to use.
            prompt (str): The prompt to provide to the model.
            system_prompt (str): The optional system prompt to give to the model
            stream (bool): If true, return a generator for streaming the response.
            response_model: Optional pydantic model for returning structured data
        
        Returns:
            str: The text generated by the model, or None if there was an issue
        """
        url = f"{self.host}/api/generate"
        data = {
            "model": model,
            "prompt": prompt,
            "stream": stream
        }
        if system_prompt: # Only add system prompt if it exists
            data['system'] = system_prompt
        if response_model: # If response_model exists, add the format parameter
            data['format'] = response_model.model_json_schema()
        try:
             response = requests.post(url, json=data, stream=stream)
             response.raise_for_status() # raise an exception for error codes

             if stream:
                  return self._process_stream(response)
             else:
                  response_json = response.json()
                  if response_model: # parse the json into a pydantic model if it exists
                      return self._parse_response(response_json, response_model)
                  else:
                       return response_json.get('response')
        except requests.exceptions.RequestException as e:
             self.logger.error(f'Error calling ollama API: {e}')
             return None

    def _parse_response(self, response_json: Dict[str, Any], response_model: Type[BaseModel]) -> BaseModel | None:
          """
          Parses the json response into a pydantic model
          """
          response_text = response_json.get('response')
          if response_text:
               try:
                    model = response_model.model_validate_json(response_text)
                    return model
               except ValidationError as e:
                    self.logger.error(f"Error validating json response: {e}")
                    return None
          self.logger.error("Could not parse the response into a pydantic model")
          return None

    def _process_stream(self, response: requests.Response) -> Generator[str, None, None]:
        """
         Process a streamed response from the ollama server
        """
        full_text = ""
        for line in response.iter_lines():
            if line:
                try:
                    json_line = json.loads(line)
                    if 'done' in json_line and json_line['done'] is True:
                         break # if done, then close the stream
                    text_chunk = json_line.get('response', "")
                    full_text += text_chunk
                    yield text_chunk # Return chunk by chunk
                except json.JSONDecodeError as e:
                     self.logger.warning(f"Error parsing json: {line} - {e}")
        yield full_text # Return all of the text

    def get_status(self):
        """
        Returns the status of the ollama client
        """
        return {
            'host': self.host
        }
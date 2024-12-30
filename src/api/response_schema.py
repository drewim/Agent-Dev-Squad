from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """
    Base model for structured responses that includes confidence.
    """
    confidence: float = Field(
         description="Confidence level on a scale from 0 to 1"
    )
    response: Optional[str] = Field(
         default=None, description="LLM response, usually a code string"
    )
    extra_data: Optional[Dict[str, Any]] = Field(
         default=None, description="Additional data fields to add"
    )
    subtasks: Optional[List[str]] = Field(
         default=None, description="List of subtasks, usually subtask ids"
    )
    feedback: Optional[str] = Field(
         default=None, description="String with feedback"
    )
    tests: Optional[str] = Field(
         default=None, description="String with python unit tests"
    )

class ArchitectResponse(BaseResponse):
     """
     Response schema for the Architect Agent
     """
     subtasks: Optional[List[str]] = Field(description="List of subtasks created")

class SeniorDevResponse(BaseResponse):
     """
     Response schema for the Senior Dev Agent
     """
     feedback: Optional[str] = Field(description="String containing feedback for a given code block")
     tests: Optional[str] = Field(default = None, description="String with tests for code")

class JuniorDevResponse(BaseResponse):
     """
     Response schema for the Junior Dev Agent
     """
     response: Optional[str] = Field(description="String containing a python code block")

class TestDevResponse(BaseResponse):
     """
     Response schema for the Test Dev Agent
     """
     tests: Optional[str] = Field(description="String containing python unit tests")
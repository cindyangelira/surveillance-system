from langchain_google_genai import ChatGoogleGenerativeAI
import base64
from pathlib import Path
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import os
from typing import Literal

from ..config import settings

api_key = settings.GOOGLE_API_KEY
os.environ['GOOGLE_API_KEY'] = api_key

class ViolenceDetection(BaseModel):
    description: str = Field(description="Detailed description of any violent or suspicious activity detected")
    threat_level: Literal["Low", "Medium", "High"] = Field(
        description="Threat level based on severity of observed violence"
    )
    recommendations: str = Field(description="Specific security actions needed in response")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "description": "No signs of violence or suspicious activity detected",
                    "threat_level": "Low",
                    "recommendations": "Continue normal monitoring"
                }
            ]
        }
    }

model = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=api_key
)

parser = PydanticOutputParser(pydantic_object=ViolenceDetection)

def encode_image(image_path):
    """Encode local image to base64."""
    image_paths = Path(__file__).parent / image_path
    with open(image_paths, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

ANALYSIS_PROMPT = """Analyze this surveillance image for signs of violence or suspicious activity.
        Look for:
        - Physical altercations or fights
        - Aggressive behavior
        - Weapons or threatening objects
        - Signs of assault or distress
        - Potential criminal activity

        Provide a detailed analysis following these guidelines for threat levels:
        - Low: Minor aggression, no immediate danger
        - Medium: Clear aggressive behavior, potential for escalation
        - High: Active violence, weapons, immediate intervention needed
        """

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a security system analyzing surveillance footage for violent incidents.
        Return the requested response object in {language}.
        {format_instructions}"""
    ),
    (
        "human", 
        [
            {
                "type": "text",
                "text": ANALYSIS_PROMPT
            },
            {
                "type": "image_url",
                "image_url": {"url": "data:image/jpeg;base64,{image_data}"},
            },
        ],
    )
])

chain = prompt | model | parser

def analyze_image_for_violence(image_path: str) -> dict:
    """
    Analyze a local image for signs of violence and return results in JSON format.
    
    Args:
        image_path (str): Path to the local image file
    
    Returns:
        dict: JSON formatted analysis results
    """
    try:
        image_data = encode_image(image_path)
        
        result = chain.invoke({
            "language": "English",
            "format_instructions": parser.get_format_instructions(),
            "image_data": image_data
        })
        
        # convert to dict for JSON serialization
        return result.model_dump()
    
    except Exception as e:
        return {
            "error": f"Error processing image: {str(e)}",
            "description": "Failed to analyze image",
            "threat_level": "Unknown",
            "recommendations": "System error - please check image and try again"
        }

# example usage
if __name__ == "__main__":
    image_path = 'test_image.jpg'
    results = analyze_image_for_violence(image_path)
    print(results)
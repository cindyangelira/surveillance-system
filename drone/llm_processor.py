from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_community.llms import GemmaCpp
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import base64
import cv2
import numpy as np
from collections import Counter

class DetectedObject(BaseModel):
    class_name: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]

class ViolenceAnalysis(BaseModel):
    num_people: int = Field(description="Number of people involved in the incident")
    violence_type: str = Field(description="Type of violence observed")
    weapons_present: bool = Field(description="Whether any weapons are visible")
    weapon_types: Optional[List[str]] = Field(description="Types of weapons observed if any")
    risk_level: str = Field(description="Assessed risk level (low/medium/high)")
    terrain_context: str = Field(description="How the terrain/location affects the situation")
    recommended_actions: List[str] = Field(description="Recommended immediate actions")

class GemmaProcessor:
    def __init__(self, model_path: str):
        self.llm = GemmaCpp(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4
        )
        
        self.parser = PydanticOutputParser(pydantic_object=ViolenceAnalysis)
        
        # define categories for classification
        self.weapon_categories = {
            'firearm': ['pistol', 'rifle', 'gun', 'shotgun', 'weapon'],
            'knife': ['knife', 'blade', 'dagger', 'sword'],
            'blunt': ['bat', 'stick', 'pipe', 'club'],
            'improvised': ['bottle', 'rock', 'brick', 'tool']
        }
        
        self.violence_indicators = {
            'physical': ['fighting', 'punching', 'kicking', 'grappling', 'assault'],
            'threatening': ['pointing', 'threatening', 'intimidating', 'aggressive'],
            'group': ['gathering', 'crowd', 'mob', 'gang']
        }
        
        self.prompt = PromptTemplate(
            template="""
            Analyze the following violent incident detected by drone surveillance:

            Location Context:
            - Latitude: {latitude}
            - Longitude: {longitude}
            - Terrain Type: {terrain_type}
            - Land Use: {land_use}

            Detection Information:
            {detections}

            Based on the above information, provide a detailed analysis of the situation.
            Consider the number of people involved, types of violence observed, presence of weapons,
            and how the terrain/location might affect the situation or response needed.

            {format_instructions}
            """,
            input_variables=["latitude", "longitude", "terrain_type", "land_use", "detections"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )

    def _format_detections(self, detections: Dict[str, Any]) -> str:
        """
        Format YOLO detections into detailed text description for LLM analysis
        
        Expected detection format:
        {
            'objects': [
                {
                    'class_name': str,
                    'confidence': float,
                    'bbox': [x1, y1, x2, y2]
                },
                ...
            ],
            'frame_info': {
                'width': int,
                'height': int,
                'timestamp': float
            }
        }
        """
        if not detections or 'objects' not in detections:
            return "No clear detections available"

        # count detected objects
        object_counts = Counter(obj['class_name'] for obj in detections['objects'])
        
        # process people and their actions
        people_info = []
        weapon_info = []
        action_info = []
        
        for obj in detections['objects']:
            class_name = obj['class_name']
            conf = obj['confidence']
            
            # process weapons
            weapon_type = None
            for category, keywords in self.weapon_categories.items():
                if any(keyword in class_name.lower() for keyword in keywords):
                    weapon_type = category
                    weapon_info.append(f"{class_name} (type: {category}, confidence: {conf:.2f})")
                    break
            
            # process violent actions
            action_type = None
            for category, keywords in self.violence_indicators.items():
                if any(keyword in class_name.lower() for keyword in keywords):
                    action_type = category
                    action_info.append(f"{class_name} (type: {category}, confidence: {conf:.2f})")
                    break
            
            # process people
            if 'person' in class_name.lower():
                people_info.append(f"Person detected (confidence: {conf:.2f})")
        
        description_parts = []
        
        # people summary
        num_people = object_counts.get('person', 0)
        if num_people > 0:
            description_parts.append(f"Detected {num_people} {'person' if num_people == 1 else 'people'}.")
        
        # weapon summary
        if weapon_info:
            description_parts.append("Weapons detected:")
            description_parts.extend(f"- {info}" for info in weapon_info)
        
        # violence/action summary
        if action_info:
            description_parts.append("Observed actions:")
            description_parts.extend(f"- {info}" for info in action_info)
        
        # spatial analysis
        if len(detections['objects']) >= 2:
            description_parts.append(self._analyze_spatial_relationships(detections['objects']))
        
        # join
        detailed_description = "\n".join(description_parts)
        
        return f"""
        Surveillance Detection Report:
        
        {detailed_description}
        
        Additional Context:
        - Scene captured at: {detections.get('frame_info', {}).get('timestamp', 'unknown time')}
        - Detection confidence levels are provided where available
        """

    def _analyze_spatial_relationships(self, objects: List[Dict]) -> str:
        """Analyze spatial relationships between detected objects"""
        # find people who are close to each other or to weapons
        relationships = []
        
        for i, obj1 in enumerate(objects):
            for obj2 in objects[i+1:]:
                # calculate distance between bounding boxes
                distance = self._calculate_box_distance(obj1['bbox'], obj2['bbox'])
                
                if distance < 0.2:  # threshold for "close" objects (20% of frame size)
                    relationships.append(
                        f"Detected {obj1['class_name']} is in close proximity to {obj2['class_name']}"
                    )
        
        if relationships:
            return "Spatial Analysis:\n- " + "\n- ".join(relationships)
        return "No significant spatial relationships detected between objects"

    def _calculate_box_distance(self, bbox1: List[float], bbox2: List[float]) -> float:
        """Calculate normalized distance between two bounding boxes"""
        # calculate centers
        center1 = [(bbox1[0] + bbox1[2])/2, (bbox1[1] + bbox1[3])/2]
        center2 = [(bbox2[0] + bbox2[2])/2, (bbox2[1] + bbox2[3])/2]
        
        # calculate Euclidean distance (normalized)
        return np.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)
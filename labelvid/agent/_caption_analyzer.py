"""Caption analyzer using LLM to extract structured information."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable

from loguru import logger

from ._llm_client import LLMClient
from ._llm_client import LLMProvider


@dataclass
class ObjectDetection:
    """Structured information about an object detection from captions."""
    
    timestamp_start: float  # Start time in seconds
    timestamp_end: float    # End time in seconds
    object_name: str        # Name of the detected object
    detection_score: float  # Confidence score for detection (0-1)
    recognition_score: float  # Confidence score for recognition (0-1)
    is_hazard: bool        # Whether the object is a hazard
    description: str       # Additional description from caption
    raw_caption: str       # Original caption text


class CaptionAnalyzer:
    """Analyze captions using LLM to extract object detection information."""
    
    def __init__(
        self,
        llm_client: LLMClient | None = None,
        provider: LLMProvider = LLMProvider.OPENAI,
        api_key: str | None = None,
    ):
        """Initialize caption analyzer.
        
        Args:
            llm_client: Pre-configured LLM client (if None, creates new one)
            provider: LLM provider to use (if llm_client is None)
            api_key: API key (if llm_client is None)
        """
        if llm_client is None:
            self._llm = LLMClient(provider=provider, api_key=api_key)
        else:
            self._llm = llm_client
    
    def analyze_captions(
        self,
        caption_segments: list,
        progress_callback: Callable[[float, str], None] | None = None,
        chunk_size: int = 20,
    ) -> list[ObjectDetection]:
        """Analyze caption segments to extract object detection information.
        
        Splits captions into fixed-size chunks and processes them to avoid token limits.
        
        Args:
            caption_segments: List of caption segments with start, end, text attributes
            progress_callback: Optional callback for progress updates (progress, message)
            chunk_size: Number of caption segments per chunk (default: 20)
            
        Returns:
            List of ObjectDetection objects
        """
        if not caption_segments:
            return []
        
        if progress_callback:
            progress_callback(0.0, "Preparing captions for analysis...")
        
        # Split captions into fixed-size chunks
        sequences = self._split_into_chunks(caption_segments, chunk_size)
        
        if not sequences:
            logger.warning("No caption sequences found after splitting")
            return []
        
        logger.info("Split captions into {} sequences", len(sequences))
        
        # Process each sequence
        all_detections = []
        for i, seq_segments in enumerate(sequences, 1):
            if progress_callback:
                progress = 0.1 + (0.8 * i / len(sequences))
                progress_callback(progress, f"Analyzing sequence {i}/{len(sequences)}...")
            
            try:
                detections = self._analyze_sequence(seq_segments)
                all_detections.extend(detections)
                logger.info("Sequence {}/{}: found {} detections", i, len(sequences), len(detections))
            except Exception as e:
                logger.error("Failed to analyze sequence {}/{}: {}", i, len(sequences), e)
                # Continue with next sequence instead of failing completely
                continue
        
        if progress_callback:
            progress_callback(1.0, f"Analysis complete! Found {len(all_detections)} detections")
        
        logger.info("Caption analysis complete: {} detections found from {} sequences", 
                   len(all_detections), len(sequences))
        return all_detections
    
    def _split_into_chunks(self, caption_segments: list, chunk_size: int = 20) -> list[list]:
        """Split caption segments into fixed-size chunks.
        
        Args:
            caption_segments: List of caption segments
            chunk_size: Number of segments per chunk (default: 20)
            
        Returns:
            List of caption segment chunks (each chunk is a list of segments)
        """
        if chunk_size <= 0:
            chunk_size = 20
        
        chunks = []
        for i in range(0, len(caption_segments), chunk_size):
            chunk = caption_segments[i:i + chunk_size]
            chunks.append(chunk)
        
        return chunks
    
    def _analyze_sequence(self, seq_segments: list) -> list[ObjectDetection]:
        """Analyze a single sequence of caption segments.
        
        Args:
            seq_segments: List of caption segments in this sequence
            
        Returns:
            List of ObjectDetection objects
        """
        # Format captions as SRT-like text
        srt_text = self._format_as_srt(seq_segments)
        
        # Create prompt
        system_prompt = """You are an expert at analyzing video captions to extract object detection information.

Your task is to extract structured object-detection events from video captions.
You must rely ONLY on the provided captions. Do not infer beyond the text.

Each caption may contain zero, one, or multiple object detections.

Participants may:
1. Report the name of an object they are tracing/detecting
2. Report detection confidence (0–5 scale)
3. Report recognition confidence (0–5 scale)
4. State whether the object is a hazard/danger
5. Report the description of the object they are tracing/detecting (e.g. position, color, shape, size, etc.) and why it is a hazard/danger
6. Say "start" when beginning to trace an object
7. Say "stop" when finishing tracing an object

However, participants may not always explicitly say "start" or "stop".
You must infer the detection time span based only on the caption timestamps and textual cues.

For each object detection mentioned in the captions, extract:
1. object_name: The name of the object being detected. If cannot be determined, set to "unknown".
2. detection_score: Confidence score for detection (0-5). If cannot be determined, set to null.
3. recognition_score: Confidence score for recognition (0-5). If cannot be determined, set to null.
4. is_hazard: Whether the object is described as a hazard/danger (true/false). If cannot be determined, set to null.
5. description: The description of the object they are tracing/detecting and why it is a hazard/danger. If cannot be determined, set to null.
6. raw_caption: The original caption text. If cannot be determined, set to null.

Rules:
1.	If multiple objects appear in one caption, output separate JSON objects.
2.	Do NOT hallucinate objects not explicitly mentioned.
3.	Do NOT add fields beyond those specified.
4.	Output must be valid JSON.
5.	Output ONLY a JSON array. No explanations. No markdown. No trailing commas.

Example output:
[
  {
    "timestamp_start": 0.0,
    "timestamp_end": 3.5,
    "object_name": "backpack",
    "detection_score": 0.95,
    "recognition_score": 0.92,
    "is_hazard": true,
    "description": "I can only see a vague shape of a bag, but I'm not sure what it is.",
    "raw_caption": "I see a backpack on the ground. It's on the left side of the screen... I'm not sure what it is."
  }
]

If no objects are detected in the captions, return an empty array: []"""

        user_prompt = f"""Analyze the following video captions and extract object detection information:

{srt_text}

Extract all object detections mentioned in the captions. Return as JSON array."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        # Get response from LLM (increased max_tokens for GPT-5 reasoning)
        response_text = self._llm.chat(messages, temperature=0.3, max_tokens=16384)
        
        # Parse JSON response
        detections = self._parse_response(response_text, seq_segments)
        
        return detections
    
    def _format_as_srt(self, segments: list) -> str:
        """Format caption segments as SRT text.
        
        Args:
            segments: List of caption segments
            
        Returns:
            SRT-formatted text
        """
        lines = []
        for i, seg in enumerate(segments, 1):
            # Format timestamp
            start = self._format_timestamp(seg.start)
            end = self._format_timestamp(seg.end)
            
            lines.append(f"{i}")
            lines.append(f"{start} --> {end}")
            lines.append(seg.text)
            lines.append("")  # Blank line
        
        return "\n".join(lines)
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds as SRT timestamp (HH:MM:SS,mmm).
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted timestamp string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _parse_response(
        self,
        response_text: str,
        caption_segments: list,
    ) -> list[ObjectDetection]:
        """Parse LLM response into ObjectDetection objects.
        
        Args:
            response_text: JSON response from LLM
            caption_segments: Original caption segments
            
        Returns:
            List of ObjectDetection objects
        """
        # Check if response is empty
        if not response_text or not response_text.strip():
            logger.error("Empty response from LLM")
            raise ValueError("Empty response from LLM. The model may have refused to respond or encountered an error.")
        
        # Clean response (remove markdown code blocks if present)
        response_text = response_text.strip()
        logger.debug("Raw LLM response (first 200 chars): {}", response_text[:200])
        
        if response_text.startswith("```"):
            # Remove markdown code blocks
            lines = response_text.split("\n")
            response_text = "\n".join(
                line for line in lines
                if not line.strip().startswith("```")
            )
            response_text = response_text.strip()
        
        # Parse JSON
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM response as JSON: {}", e)
            logger.error("Response text (first 500 chars): {}", response_text[:500])
            logger.error("Response text length: {}", len(response_text))
            raise ValueError(f"Invalid JSON response from LLM: {e}\n\nResponse preview: {response_text[:200]}")
        
        # Convert to ObjectDetection objects
        detections = []
        for item in data:
            try:
                # Find the raw caption text for this timestamp
                raw_caption = ""
                for seg in caption_segments:
                    if (seg.start <= item["timestamp_start"] <= seg.end or
                        seg.start <= item["timestamp_end"] <= seg.end):
                        raw_caption = seg.text
                        break
                
                # Handle None values properly
                detection_score = item.get("detection_score")
                if detection_score is not None:
                    detection_score = float(detection_score)
                
                recognition_score = item.get("recognition_score")
                if recognition_score is not None:
                    recognition_score = float(recognition_score)
                
                is_hazard = item.get("is_hazard")
                if is_hazard is not None:
                    is_hazard = bool(is_hazard)
                
                description = item.get("description", "")
                if description is None:
                    description = ""
                
                detection = ObjectDetection(
                    timestamp_start=float(item["timestamp_start"]),
                    timestamp_end=float(item["timestamp_end"]),
                    object_name=str(item["object_name"]),
                    detection_score=detection_score,
                    recognition_score=recognition_score,
                    is_hazard=is_hazard,
                    description=str(description),
                    raw_caption=raw_caption,
                )
                detections.append(detection)
                logger.debug("Parsed detection: {} (det={}, rec={}, hazard={})", 
                           item["object_name"], detection_score, recognition_score, is_hazard)
            except (KeyError, ValueError, TypeError) as e:
                logger.warning("Skipping invalid detection item: {} - {}", item, e)
                continue
        
        return detections
    
    def export_to_json(
        self,
        detections: list[ObjectDetection],
        output_path: str,
    ) -> None:
        """Export detections to JSON file.
        
        Args:
            detections: List of ObjectDetection objects
            output_path: Path to output JSON file
        """
        data = []
        for det in detections:
            data.append({
                "timestamp_start": det.timestamp_start,
                "timestamp_end": det.timestamp_end,
                "object_name": det.object_name,
                "detection_score": det.detection_score,
                "recognition_score": det.recognition_score,
                "is_hazard": det.is_hazard,
                "description": det.description,
                "raw_caption": det.raw_caption,
            })
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info("Exported {} detections to {}", len(detections), output_path)

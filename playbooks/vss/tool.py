"""
Video Search + Summarization (VSS) Tool
Video analysis tool with search and summarization capabilities

Dependencies: Agent 8 (multi-modal processing)
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import base64
import json
import hashlib
import logging

logger = logging.getLogger(__name__)


@dataclass
class VideoFrame:
    """Represents a video frame"""
    frame_number: int
    timestamp: float
    image_data: Optional[bytes] = None
    embedding: Optional[List[float]] = None
    description: Optional[str] = None


@dataclass
class VideoSegment:
    """Represents a segment of video"""
    start_time: float
    end_time: float
    frames: List[VideoFrame] = field(default_factory=list)
    transcript: Optional[str] = None
    summary: Optional[str] = None
    keywords: List[str] = field(default_factory=list)


@dataclass
class VideoMetadata:
    """Video metadata"""
    video_id: str
    title: str
    duration: float
    fps: float
    resolution: Tuple[int, int]
    format: str
    file_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SearchResult:
    """Video search result"""
    video_id: str
    segment: VideoSegment
    relevance_score: float
    match_type: str  # "visual", "transcript", "semantic"


@dataclass
class VideoSummary:
    """Complete video summary"""
    video_id: str
    title: str
    duration: float
    overall_summary: str
    segment_summaries: List[Dict[str, Any]]
    key_moments: List[Dict[str, Any]]
    topics: List[str]
    generated_at: datetime = field(default_factory=datetime.now)


class MultiModalProcessor:
    """
    Multi-modal video processing using Agent 8
    """

    def __init__(self, agent_url: str = "http://localhost:8888"):
        self.agent_url = agent_url

    async def extract_frames(
        self,
        video_path: str,
        frame_rate: float = 1.0
    ) -> List[VideoFrame]:
        """
        Extract frames from video at specified rate

        Args:
            video_path: Path to video file
            frame_rate: Frames per second to extract

        Returns:
            List of extracted frames
        """
        # In production, this would use actual video processing
        # For demo, return placeholder frames
        logger.info(f"Extracting frames from {video_path} at {frame_rate} fps")

        # Simulate frame extraction
        duration = 60.0  # Demo: 60 second video
        num_frames = int(duration * frame_rate)

        frames = []
        for i in range(num_frames):
            frame = VideoFrame(
                frame_number=i,
                timestamp=i / frame_rate
            )
            frames.append(frame)

        return frames

    async def analyze_frame(self, frame_data: bytes) -> Dict[str, Any]:
        """
        Analyze a video frame using multi-modal model

        Args:
            frame_data: Frame image data

        Returns:
            Analysis results with description and features
        """
        try:
            # Encode frame as base64
            frame_b64 = base64.b64encode(frame_data).decode('utf-8')

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.agent_url}/analyze_image",
                    json={
                        "image": frame_b64,
                        "task": "describe"
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Frame analysis failed: {response.status}")
                        return {
                            "description": "Frame analysis unavailable",
                            "objects": [],
                            "scene": "unknown"
                        }
        except Exception as e:
            logger.error(f"Frame analysis error: {e}")
            return {
                "description": "Error analyzing frame",
                "objects": [],
                "scene": "unknown"
            }

    async def generate_frame_embedding(self, frame_data: bytes) -> List[float]:
        """
        Generate embedding for video frame

        Args:
            frame_data: Frame image data

        Returns:
            Embedding vector
        """
        try:
            frame_b64 = base64.b64encode(frame_data).decode('utf-8')

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.agent_url}/embed_image",
                    json={"image": frame_b64},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("embedding", [])
                    return []
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            return []

    async def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe audio from video

        Args:
            audio_path: Path to audio file

        Returns:
            Transcription text
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.agent_url}/transcribe",
                    json={"audio_path": audio_path},
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("text", "")
                    return ""
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""


class VideoSummarizer:
    """
    Service for summarizing video content
    """

    def __init__(self, llm_url: str = "http://localhost:8000"):
        self.llm_url = llm_url

    async def summarize_segment(
        self,
        segment: VideoSegment,
        frame_descriptions: List[str]
    ) -> str:
        """
        Generate summary for a video segment

        Args:
            segment: Video segment
            frame_descriptions: Descriptions of frames in segment

        Returns:
            Segment summary
        """
        # Build context
        context_parts = []

        if frame_descriptions:
            context_parts.append("Visual content:")
            for i, desc in enumerate(frame_descriptions[:5]):  # Limit to 5
                context_parts.append(f"  Frame {i+1}: {desc}")

        if segment.transcript:
            context_parts.append(f"\nTranscript: {segment.transcript}")

        context = "\n".join(context_parts)

        prompt = f"""Summarize the following video segment content in 2-3 sentences:

{context}

Summary:"""

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.llm_url}/generate",
                    json={
                        "prompt": prompt,
                        "model": "gpt-4",
                        "max_tokens": 150,
                        "temperature": 0.5
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("text", "Summary unavailable")
                    return "Summary generation failed"
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return f"Error: {str(e)}"

    async def generate_overall_summary(
        self,
        segment_summaries: List[str],
        metadata: VideoMetadata
    ) -> str:
        """
        Generate overall video summary from segment summaries

        Args:
            segment_summaries: List of segment summaries
            metadata: Video metadata

        Returns:
            Overall summary
        """
        segments_text = "\n".join([
            f"Segment {i+1}: {summary}"
            for i, summary in enumerate(segment_summaries)
        ])

        prompt = f"""Create a comprehensive summary of this video:

Title: {metadata.title}
Duration: {metadata.duration:.1f} seconds

Segment summaries:
{segments_text}

Provide a cohesive 3-4 sentence summary of the entire video:"""

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.llm_url}/generate",
                    json={
                        "prompt": prompt,
                        "model": "gpt-4",
                        "max_tokens": 200,
                        "temperature": 0.5
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("text", "Overall summary unavailable")
                    return "Summary generation failed"
        except Exception as e:
            logger.error(f"Overall summarization error: {e}")
            return f"Error: {str(e)}"


class VideoSearchEngine:
    """
    Search engine for video content
    """

    def __init__(self):
        self.video_index: Dict[str, List[VideoSegment]] = {}
        self.frame_embeddings: Dict[str, List[Tuple[int, List[float]]]] = {}

    def index_video(
        self,
        video_id: str,
        segments: List[VideoSegment],
        frame_embeddings: List[Tuple[int, List[float]]]
    ):
        """
        Index video for search

        Args:
            video_id: Video identifier
            segments: Video segments
            frame_embeddings: Frame embeddings for visual search
        """
        self.video_index[video_id] = segments
        self.frame_embeddings[video_id] = frame_embeddings
        logger.info(f"Indexed video {video_id} with {len(segments)} segments")

    async def search_transcript(
        self,
        query: str,
        video_ids: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """
        Search video transcripts

        Args:
            query: Search query
            video_ids: Optional list of video IDs to search

        Returns:
            List of search results
        """
        results = []
        query_lower = query.lower()

        videos_to_search = video_ids if video_ids else list(self.video_index.keys())

        for video_id in videos_to_search:
            segments = self.video_index.get(video_id, [])
            for segment in segments:
                if segment.transcript and query_lower in segment.transcript.lower():
                    # Simple keyword matching
                    score = segment.transcript.lower().count(query_lower) / len(segment.transcript.split())
                    results.append(SearchResult(
                        video_id=video_id,
                        segment=segment,
                        relevance_score=score,
                        match_type="transcript"
                    ))

        # Sort by relevance
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results

    async def search_visual(
        self,
        query_embedding: List[float],
        video_ids: Optional[List[str]] = None,
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        Search by visual similarity

        Args:
            query_embedding: Query image embedding
            video_ids: Optional list of video IDs to search
            top_k: Number of results to return

        Returns:
            List of search results
        """
        # Placeholder for visual search
        # In production, this would compute cosine similarity with frame embeddings
        results = []
        return results[:top_k]


class VSSSystem:
    """
    Complete Video Search + Summarization system
    """

    def __init__(
        self,
        multimodal_url: str = "http://localhost:8888",
        llm_url: str = "http://localhost:8000",
        port: int = 8081
    ):
        self.multimodal_url = multimodal_url
        self.llm_url = llm_url
        self.port = port

        self.processor = MultiModalProcessor(multimodal_url)
        self.summarizer = VideoSummarizer(llm_url)
        self.search_engine = VideoSearchEngine()

        self.videos: Dict[str, VideoMetadata] = {}

    async def ingest_video(
        self,
        video_path: str,
        video_id: Optional[str] = None,
        title: Optional[str] = None
    ) -> VideoMetadata:
        """
        Ingest and process a video

        Args:
            video_path: Path to video file
            video_id: Optional video ID (generated if not provided)
            title: Optional video title

        Returns:
            Video metadata
        """
        if video_id is None:
            video_id = hashlib.sha256(video_path.encode()).hexdigest()[:16]

        if title is None:
            title = Path(video_path).stem

        # Create metadata
        metadata = VideoMetadata(
            video_id=video_id,
            title=title,
            duration=60.0,  # Placeholder
            fps=30.0,
            resolution=(1920, 1080),
            format="mp4",
            file_path=video_path
        )

        self.videos[video_id] = metadata

        logger.info(f"Ingested video: {video_id} ({title})")

        # Extract and process frames (async in background)
        # In production, this would be a background task
        # frames = await self.processor.extract_frames(video_path, frame_rate=1.0)

        return metadata

    async def generate_summary(self, video_id: str) -> VideoSummary:
        """
        Generate comprehensive video summary

        Args:
            video_id: Video identifier

        Returns:
            Video summary
        """
        metadata = self.videos.get(video_id)
        if not metadata:
            raise ValueError(f"Video {video_id} not found")

        # For demo, create sample segments and summaries
        num_segments = 4
        segment_duration = metadata.duration / num_segments

        segment_summaries = []
        for i in range(num_segments):
            start_time = i * segment_duration
            end_time = (i + 1) * segment_duration

            segment = VideoSegment(
                start_time=start_time,
                end_time=end_time,
                transcript=f"Segment {i+1} transcript placeholder",
                summary=f"This segment covers content from {start_time:.1f}s to {end_time:.1f}s"
            )

            segment_summaries.append({
                "start_time": start_time,
                "end_time": end_time,
                "summary": segment.summary
            })

        # Generate overall summary
        overall_summary = await self.summarizer.generate_overall_summary(
            [s["summary"] for s in segment_summaries],
            metadata
        )

        summary = VideoSummary(
            video_id=video_id,
            title=metadata.title,
            duration=metadata.duration,
            overall_summary=overall_summary,
            segment_summaries=segment_summaries,
            key_moments=[
                {"timestamp": 10.0, "description": "Key moment 1"},
                {"timestamp": 30.0, "description": "Key moment 2"}
            ],
            topics=["Technology", "Analytics", "Data Processing"]
        )

        return summary

    async def search(
        self,
        query: str,
        search_type: str = "transcript"
    ) -> List[SearchResult]:
        """
        Search videos

        Args:
            query: Search query
            search_type: Type of search ("transcript", "visual", "semantic")

        Returns:
            List of search results
        """
        if search_type == "transcript":
            return await self.search_engine.search_transcript(query)
        elif search_type == "visual":
            # Would need to convert query to embedding
            return []
        else:
            return []

    def get_video_list(self) -> List[Dict[str, Any]]:
        """Get list of all videos"""
        return [
            {
                "video_id": vid_id,
                "title": metadata.title,
                "duration": metadata.duration,
                "created_at": metadata.created_at.isoformat()
            }
            for vid_id, metadata in self.videos.items()
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        total_duration = sum(v.duration for v in self.videos.values())

        return {
            "num_videos": len(self.videos),
            "total_duration_seconds": total_duration,
            "total_duration_formatted": str(timedelta(seconds=int(total_duration))),
            "port": self.port,
            "status": "ready"
        }


async def main():
    """Demo VSS system"""
    print("Video Search + Summarization (VSS) Tool")
    print("=" * 50)

    # Initialize system
    vss = VSSSystem(
        multimodal_url="http://localhost:8888",
        llm_url="http://localhost:8000",
        port=8081
    )

    # Ingest sample videos
    sample_videos = [
        ("video1.mp4", "Introduction to Apache Spark"),
        ("video2.mp4", "Spark MLlib Tutorial"),
        ("video3.mp4", "Real-time Analytics with Spark Streaming")
    ]

    print("\nIngesting videos...")
    for video_path, title in sample_videos:
        metadata = await vss.ingest_video(video_path, title=title)
        print(f"  ✓ {metadata.title} ({metadata.duration:.1f}s)")

    # System statistics
    stats = vss.get_stats()
    print("\n" + "=" * 50)
    print("System Statistics:")
    print(f"  Videos indexed: {stats['num_videos']}")
    print(f"  Total duration: {stats['total_duration_formatted']}")
    print(f"  Status: {stats['status']}")

    # Generate summary for a video
    print("\n" + "=" * 50)
    print("Video Summary Example:")
    print("=" * 50)

    video_id = list(vss.videos.keys())[0]
    summary = await vss.generate_summary(video_id)

    print(f"\nTitle: {summary.title}")
    print(f"Duration: {summary.duration:.1f}s")
    print(f"\nOverall Summary:")
    print(f"  {summary.overall_summary}")

    print(f"\nSegment Summaries:")
    for seg in summary.segment_summaries:
        print(f"  [{seg['start_time']:.1f}s - {seg['end_time']:.1f}s]: {seg['summary']}")

    print(f"\nKey Moments:")
    for moment in summary.key_moments:
        print(f"  {moment['timestamp']:.1f}s: {moment['description']}")

    print(f"\nTopics: {', '.join(summary.topics)}")

    # Search example
    print("\n" + "=" * 50)
    print("Search Example:")
    print("=" * 50)

    query = "Spark MLlib"
    print(f"\nQuery: {query}")
    print(f"Search type: transcript")
    print(f"Results: (search functionality requires video transcripts)")


if __name__ == "__main__":
    asyncio.run(main())

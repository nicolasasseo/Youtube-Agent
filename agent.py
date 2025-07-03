"""
YouTube AI Agent

This module implements an interactive AI agent that can fetch and analyze YouTube video transcripts.
The agent uses the YouTube Transcript API to extract video transcripts and provides an interactive
chat interface for users to ask questions about YouTube videos.

Dependencies:
    - youtube-transcript-api: For fetching YouTube video transcripts
    - agents: Custom AI agent framework
    - openai: For AI response types
    - python-dotenv: For environment variable management

Usage:
    python agent.py

Environment Variables:
    The agent requires appropriate API keys to be set in a .env file for the underlying
    AI framework to function properly.

Author: YouTube AI Agent
Version: 1.0
"""

from youtube_transcript_api._api import YouTubeTranscriptApi
import re
from agents import Agent, function_tool, Runner, ItemHelpers, RunContextWrapper
from openai.types.responses import ResponseTextDeltaEvent
from dotenv import load_dotenv
import asyncio

# Load environment variables from .env file (API keys, configuration, etc.)
load_dotenv()

# Agent instructions that define its role and capabilities
instructions = "You provide help with tasks related to YouTube videos."

@function_tool
def fetch_youtube_transcript(url: str) -> str:
    """
    Extract transcript with timestamps from a YouTube video URL and format it for LLM consumption.
    
    This function takes a YouTube URL, extracts the video ID using regex pattern matching,
    fetches the transcript using the YouTube Transcript API, and formats it with timestamps
    for easy reading and analysis.
    
    Args:
        url (str): The URL of the YouTube video. Supports both youtube.com and youtu.be formats:
                  - https://www.youtube.com/watch?v=VIDEO_ID
                  - https://youtu.be/VIDEO_ID
                  
    Returns:
        str: Formatted transcript with timestamps, where each entry is on a new line 
             in the format: "[MM:SS] Transcript text"
             
    Raises:
        ValueError: If the URL doesn't contain a valid YouTube video ID
        Exception: If there's an error fetching the transcript (video unavailable, 
                  no transcript available, API issues, etc.)
                  
    Example:
        >>> transcript = fetch_youtube_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        >>> print(transcript)
        [00:00] Never gonna give you up
        [00:02] Never gonna let you down
        ...
    """
    # Regular expression pattern to extract 11-character YouTube video ID from various URL formats
    # (?:v=|\/) - Non-capturing group that matches either "v=" or "/"
    # ([0-9A-Za-z_-]{11}) - Capturing group for exactly 11 alphanumeric/underscore/hyphen characters
    # .* - Match any remaining characters in the URL
    video_id_pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    video_id_match = re.match(video_id_pattern, url)
    
    if not video_id_match:
        raise ValueError("Invalid YouTube URL. Please provide a valid YouTube video URL.")
    
    # Extract the video ID from the regex match
    video_id = video_id_match.group(1)
    
    try:
        # Fetch transcript data from YouTube using the video ID
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        formatted_entries = []
        
        # Process each transcript entry and format with timestamps
        for entry in transcript:
            # Convert start time (in seconds) to minutes and seconds
            minutes = int(entry['start'] // 60)  # Floor division for whole minutes
            seconds = int(entry['start'] % 60)   # Modulo for remaining seconds
            
            # Format timestamp as [MM:SS] with zero-padding
            timestamp = f"[{minutes:02d}:{seconds:02d}]"
            
            # Combine timestamp with transcript text
            formatted_entries.append(f"{timestamp} {entry['text']}")
        
        # Join all entries with newlines for clean formatting
        return "\n".join(formatted_entries)
        
    except Exception as e:
        raise Exception(f"Error fetching transcript: {str(e)}. This could be due to: "
                       f"video not found, transcript not available, or API limitations.")

# Create the AI agent instance with configuration
agent = Agent(
    name="YouTube Transcript Agent",
    instructions=instructions,
    tools=[fetch_youtube_transcript],  # Provide the transcript fetching tool
)

async def main() -> None:
    """
    Main interactive loop for the YouTube Transcript Agent.
    
    This function implements a chat-based interface where users can interact with the AI agent
    to ask questions about YouTube videos. The agent can fetch transcripts and provide analysis
    based on the video content.
    
    The function handles:
    - User input collection and validation
    - Conversation history management
    - Streaming AI responses
    - Tool execution feedback
    - Graceful exit handling
    
    Flow:
        1. Display welcome message and instructions
        2. Enter interactive loop:
           - Get user input
           - Process input through AI agent
           - Stream response in real-time
           - Handle tool calls (transcript fetching)
           - Update conversation history
        3. Handle exit commands gracefully
        
    Returns:
        None
        
    Note:
        This function runs indefinitely until the user types an exit command.
    """
    # Initialize conversation history - stores all user and agent messages
    input_items = []
    
    # Display welcome message and usage instructions
    print("== YouTube Transcript Agent ==")
    print("Type 'exit' to end the conversation")
    print("Ask me anything about YouTube videos!")

    # Main interactive loop
    while True:
        # Get user input and clean whitespace
        user_input = input("\nYou: ").strip()
        
        # Add user message to conversation history
        input_items.append({"content": user_input, "role": "user"})
        
        # Check for exit commands (case-insensitive)
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye!")
            break
            
        # Skip empty inputs
        if not user_input:
            continue
            
        # Start agent response (print without newline for streaming effect)
        print("\nAgent: ", end="", flush=True)
        
        # Run the agent with streaming responses
        result = Runner.run_streamed(agent, input=input_items)
        
        # Process streaming events from the agent
        async for event in result.stream_events():
            # Handle different types of streaming events
            
            # Raw text response from the AI (character-by-character streaming)
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                print(event.data.delta, end="", flush=True)
                
            # Agent state updates (can be ignored for display purposes)
            elif event.type == "agent_updated_stream_event":
                continue
                
            # Tool execution and response events
            elif event.type == "run_item_stream_event":
                # Tool is being called (transcript fetching started)
                if event.item.type == "tool_call_item":
                    print("\n-- Fetching transcript...")
                    
                # Tool execution completed (transcript fetched)
                elif event.item.type == "tool_call_output_item":
                    # Add transcript to conversation context for agent to reference
                    input_items.append({
                        "content": f"Transcript:\n{event.item.output}", 
                        "role": "system"
                    })
                    print("-- Transcript fetched.")
                    
                # Final agent message (add to conversation history)
                elif event.item.type == "message_output_item":
                    input_items.append({
                        "content": f"{event.item.raw_item}", 
                        "role": "assistant"
                    })
                else:
                    # Handle any other event types (future extensibility)
                    pass 

        # Add newline after each complete response
        print("\n")

# Entry point - run the async main function
if __name__ == "__main__":
    asyncio.run(main())

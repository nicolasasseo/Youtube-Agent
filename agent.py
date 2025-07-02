from youtube_transcript_api import YouTubeTranscriptApi
import re
from agents import Agent, function_tool, Runner, ItemHelpers, RunContextWrapper
from openai.types.responses import ResponseTextDeltaEvent
from dotenv import load_dotenv
import asyncio

load_dotenv()

instructions = "You provide help with tasks related to YouTube videos."
#define tool
@function_tool
def fetch_youtube_transcript(url: str) -> str:
  """
  Extract transcript with timestamps from a YouTube video URL and format it for LLM consumption
  Args:
    url: str - The URL of the YouTube video
  Returns:
    str - Formatted transcript with timestamps, where each entry is on a new line in the format: "[MM:SS] Transcript text"
  Raises:
    ValueError: If the URL is invalid
  """
  # extract video ID from URL
  video_id_pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
  video_id_match = re.match(video_id_pattern, url)
  if not video_id_match:
    raise ValueError("Invalid YouTube URL")
  video_id = video_id_match.group(1)
  try:
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    formatted_entries = []
    for entry in transcript:
      minutes = int(entry['start'] // 60)
      seconds = int(entry['start'] % 60)
      timestamp = f"[{minutes:02d}:{seconds:02d}]"
      formatted_entries.append(f"{timestamp} {entry['text']}")
    return "\n".join(formatted_entries)
  except Exception as e:
    raise Exception(f"Error fetching transcript: {str(e)}")

agent = Agent(
  name="YouTube Transcript Agent",
  instructions=instructions,
  tools=[fetch_youtube_transcript],
) 

async def main():
  input_items = []
  print("== YouTube Transcript Agent ==")
  print("Type 'exit' to end the conversation")
  print("Ask me anything about YouTube videos!")

  while True:
    user_input = input("\nYou: ").strip()
    input_items.append({"content": user_input, "role": "user"})
    if user_input.lower() in ["exit", "quit", "bye"]:
      print("Goodbye!")
      break
    if not user_input:
      continue
    print("\nAgent: ", end="", flush=True)
    result = Runner.run_streamed(agent, input=input_items)
    async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                print(event.data.delta, end="", flush=True)
            elif event.type == "agent_updated_stream_event":
                continue
            elif event.type == "run_item_stream_event":
                if event.item.type == "tool_call_item":
                    print("\n-- Fetching transcript...")
                elif event.item.type == "tool_call_output_item":
                    input_items.append({"content": f"Transcript:\n{event.item.output}", "role": "system"})
                    print("-- Transcript fetched.")
                elif event.item.type == "message_output_item":
                    input_items.append({"content": f"{event.item.raw_item}", "role": "assistant"})
                else:
                    pass 

    print("\n")

if __name__ == "__main__":
  asyncio.run(main())
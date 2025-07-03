# YouTube AI Agent

This project is an interactive command-line AI agent that helps you fetch and analyze YouTube video transcripts. It uses the YouTube Transcript API to extract transcripts and provides a chat interface for asking questions about YouTube videos.

## Features

- Fetches YouTube video transcripts by URL
- Formats transcripts with timestamps
- Interactive chat interface
- Extensible with additional tools

## Requirements

- Python 3.8+
- [youtube-transcript-api](https://pypi.org/project/youtube-transcript-api/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- OpenAI-compatible agent framework (custom `agents` module)

## Setup

1. **Clone the repository**
2. **Install dependencies:**
   ```bash
   pip install youtube-transcript-api python-dotenv
   # Plus any requirements for your custom agents framework
   ```
3. **Set up your `.env` file** with any required API keys or environment variables for your agent framework.

## Usage

Run the agent from the command line:

```bash
python agent.py
```

You will see a prompt:

```
== YouTube Transcript Agent ==
Type 'exit' to end the conversation
Ask me anything about YouTube videos!
```

Type a YouTube video URL or ask a question. The agent will fetch the transcript and respond interactively.

## Example

```
You: https://www.youtube.com/watch?v=dQw4w9WgXcQ
Agent:
-- Fetching transcript...
-- Transcript fetched.
[00:00] Never gonna give you up
[00:02] Never gonna let you down
...
```

## Notes

- The agent requires a custom `agents` framework and may need an OpenAI API key or similar credentials.
- Only videos with available transcripts can be processed.

## License

MIT (or specify your license here)

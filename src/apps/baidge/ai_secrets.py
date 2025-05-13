# OpenAI API key - required for the app to work (used for transcription and reading)
# - you can get one at https://platform.openai.com/ - create account, prepay 5 USD credits, create project, generate API key)
OPENAI_KEY = ""

# Perplexity API key - needed to use Perplexity for answering (AI answers based on current web search and reasoning)
# - you can get one at https://perplexity.ai/ - account settings and API section; requires setting payment method
# (if you're lucky to have Perplexity Pro account - 5 USD monthly credit for API is included)
PERPLEXITY_KEY = ""

# The link to API webhook to your automation server (e.g. N8N, can be also Make.com, Zapier, etc.)
# - the app will send JSON with only one element named "message" containing the transcribed text
# - the app will show (and read) the answer sent in JSON as element named "output"
AUTOMATION_URL = ""
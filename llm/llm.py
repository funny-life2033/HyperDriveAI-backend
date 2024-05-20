from api.models import ChatRoom
from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI
import vertexai
from vertexai.language_models import ChatModel, InputOutputTextPair
import replicate
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

# vertexai.init(project="patentllm", location="us-central1")
client = OpenAI()
# chat_model = ChatModel.from_pretrained("chat-bison")
parameters = {
    "candidate_count": 1,
    "max_output_tokens": 1024,
    "temperature": 0.2,
    "top_p": 0.8,
    "top_k": 40,
}


def generate_answer(room, question):
    print(room.bot.base.model)

    # GPT - 3.5
    if room.bot.base.model == "gpt-3.5-turbo":
        completion = client.chat.completions.create(
            model=room.bot.base.model,
            messages=[
                {"role": "system", "content": room.bot.behavior},
                {"role": "user", "content": question},
            ],
        )
        return completion.choices[0].message.content

    # Google PaLM 2
    if room.bot.base.model == "chat-bison":
        # chat = chat_model.start_chat(
        #     context=room.bot.behavior,
        # )
        # response = chat.send_message(question, **parameters)
        # return response.text
        return "model doesn't exist"

    # Llama 2 (llama-2-70b)
    if room.bot.base.model == "llama-2-70b":
        output = replicate.run(
            "meta/llama-2-70b:a52e56fee2269a78c9279800ec88898cecb6c8f1df22a6483132bea266648f00",
            input={"prompt": question},
        )
        answer = ""
        for item in output:
            answer = answer + item
        return answer

    # Claude 2 (claude-2)
    if room.bot.base.model == "claude-2":
        anthropic = Anthropic()
        output = anthropic.completions.create(
            prompt=f"{HUMAN_PROMPT} {question} {AI_PROMPT}",
            max_tokens_to_sample=300,
            model=room.bot.base.model,
            stream=True,
        )
        answer = ""
        for item in output:
            answer = answer + item
        return answer

    # Claude Instant (claude-instant-1)
    if room.bot.base.model == "claude-instant-1":
        anthropic = Anthropic()
        output = anthropic.completions.create(
            prompt=f"{HUMAN_PROMPT} {question} {AI_PROMPT}",
            max_tokens_to_sample=300,
            model=room.bot.base.model,
            stream=True,
        )
        answer = ""
        for item in output:
            answer = answer + item
        return answer

    return "Engine not implemented yet"

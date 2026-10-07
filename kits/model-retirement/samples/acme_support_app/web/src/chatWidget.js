// Backend route for the website chat widget.
// FICTIONAL SAMPLE CODE for the model-retirement starter kit portfolio.
import { streamText } from "ai";
import { openai } from "@ai-sdk/openai";

export async function POST(req) {
  const { messages } = await req.json();
  const result = streamText({
    model: openai("partner-chat-model-x"),
    system:
      "You are the Acme Home Goods website assistant. Answer questions about orders, delivery and returns.",
    messages,
    temperature: 0.5,
    maxTokens: 256,
  });
  return result.toDataStreamResponse();
}

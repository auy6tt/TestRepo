// Draft a reply for the support agent to check and send.
// FICTIONAL SAMPLE CODE for the model-retirement starter kit portfolio.
import OpenAI from "openai";

const openai = new OpenAI(); // reads the API key from the environment

const REPLY_MODEL = process.env.REPLY_MODEL ?? "old-model-v1";

export async function draftReply(ticket: string, articles: string[]): Promise<string> {
  const completion = await openai.chat.completions.create({
    model: REPLY_MODEL,
    temperature: 0.7,
    top_p: 0.95,
    max_tokens: 400,
    messages: [
      {
        role: "system",
        content:
          "Write a short, friendly reply for an Acme Home Goods support agent to send. " +
          "Use the help articles when they apply. Do not promise anything the articles do not say.",
      },
      { role: "user", content: `Ticket:\n${ticket}\n\nHelp articles:\n${articles.join("\n---\n")}` },
    ],
  });
  return completion.choices[0].message.content ?? "";
}

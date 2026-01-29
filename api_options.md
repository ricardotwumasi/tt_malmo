# Free-tier AI API options (Jan 2026)

This note collects *legitimate* ways to call modern AI models via an API at **$0 cost** (either an always-free tier with quotas, or time-limited promotional credits), with the **clearest published limits** I could verify from primary documentation.

“Free” comes in at least three distinct flavours.

1) **Always-free quota** (no payment method needed): You can keep using it indefinitely, but within hard caps (requests per minute, requests per day, tokens per day, compute units per day).

2) **Promo credits** (time-limited, sometimes requiring phone verification or a business email): You get a small balance, then it becomes paid.

3) **Free access to models through an aggregator** (e.g., OpenRouter): You may get access to multiple “:free” model variants, but rate limits apply at the platform level and availability can change.

The tables below focus on “frontier-ish” capability, meaning access to strong reasoning/coding/chat models (often open-weight) rather than only small utility models.

---

## Summary table

| Provider | What you get for free | Examples of “most capable” models you can call for free | Published free limits (headline) | Notes |
|---|---|---|---|---|
| **OpenRouter** | Always-free access to models with `:free` suffix | Free collection includes models like **DeepSeek R1 variants** and **GLM 4.5 Air** (catalog changes) | **20 RPM**, and typically **50 free requests/day** unless you have purchased ≥10 credits (then 1000/day) | Best single “free gateway” for sampling many large open(-ish) models quickly. |
| **Cerebras Inference API** | Always-free tier for supported models | **Llama 3.1 8B** (and other large open models depending on catalog) | Example model shows **30 requests/min**, **60k input tokens/min**, and **1M daily tokens** on free tier | Extremely fast inference; limits are token-based and model-specific pages show the current caps. |
| **Cloudflare Workers AI** | Always-free compute allowance | Hosted open models including **Llama 3.x 70B**, **DeepSeek distills**, etc. | **10,000 Neurons/day** free | “Neurons” is Cloudflare’s compute unit; practical throughput depends heavily on model choice and output length. |
| **Hugging Face Inference Providers** | Always-free starter credits | Model access depends on provider routing; some large models may be available depending on your routing choice | “Past the free-tier credits” you pay; free credit amount is plan-dependent (see docs) | Great for experimentation, but the always-free amount is small and not designed for heavy use. |
| **Vercel AI Gateway** | Always-free monthly credit | “Any model from our model list” via gateway routing | **$5 monthly credit** (with conditions) | Handy if you already deploy on Vercel; credit disappears once you become a paid customer. |
| **Google Gemini API (AI Studio)** | Always-free *developer* access in AI Studio tier | Models such as **Gemini Flash(-Lite)** class (exact set changes) | Rate limits exist and vary by model; Google directs you to view them in the console | Google’s free tier is real, but model-by-model numeric caps were not consistently exposed in the public docs I could retrieve. |
| **NVIDIA API Catalog (build.nvidia.com / NIM trial)** | Promo/trial credits | NIM-hosted endpoints (varies) | **1000 credits on signup**, trial experience capped at **5000 free API credits** (as described by NVIDIA staff) | “Credits” are NVIDIA’s unit; extra credits may require business-email verification and a trial. |
| **Hyperbolic** | Small promo credit | Offers very large open models (catalog evolves) | **$1 promo credit** for phone verification; some models have explicit RPM limits by user tier | Useful for quick taste-tests; larger projects typically require deposit. |
| **Fireworks AI** | Promo credit on signup | Serverless inference across many open models | Docs confirm new users receive free credits and reference “$1 credit” depletion in FAQ | The exact amount can change; treat as a short on-ramp rather than a stable free tier. |
| **OpenAI API** | **Not** a free tier (generally) | N/A | Minimum **$5** credit purchase for prepaid billing | OpenAI is frontier-grade, but it is usually not the “free tier” route for API testing. |

---

## OpenRouter (free `:free` models)

OpenRouter explicitly publishes platform-level limits for free model variants.

Headline limits for `:free` models are **20 requests per minute** and **50 free requests per day** if you have purchased less than 10 credits; buying at least 10 credits raises the daily free-model limit to 1000 requests/day.  
Sources: OpenRouter API limits documentation and pricing/FAQ pages.  
https://openrouter.ai/docs/api/reference/limits  
https://openrouter.ai/pricing  
https://openrouter.ai/docs/faq

To find “most capable” free options at any moment, OpenRouter maintains a curated collection of free models.  
Source:  
https://openrouter.ai/collections/free-models

Practical note: model quality and availability can fluctuate because these are routed across providers; for reliable benchmarking, pin a specific model ID and record provider metadata.

---

## Cerebras Inference API (always-free token quota)

Cerebras publishes rate limits and daily token caps on each model’s documentation page. For example, the **Llama 3.1 8B** page lists a **Free** tier of **30 requests/min**, **60k input tokens/min**, and **1M daily tokens** (plus context-window constraints).  
Source:  
https://inference-docs.cerebras.ai/models/llama-31-8b

Cerebras has also publicly described providing **1 million free tokens daily** at launch.  
Source:  
https://www.cerebras.ai/blog/introducing-cerebras-inference-ai-at-instant-speed

---

## Cloudflare Workers AI (always-free 10,000 Neurons/day)

Cloudflare states that Workers AI is included on the Free plan with **10,000 Neurons per day at no charge**, resetting daily at **00:00 UTC**.  
Source:  
https://developers.cloudflare.com/workers-ai/platform/pricing/

Cloudflare’s model catalog changes over time, but their pricing page lists many currently hosted LLMs (including 70B-class) and the per-token neuron mapping, which you can use to estimate how far 10,000 neurons goes.

---

## Hugging Face Inference Providers (small always-free credits)

Hugging Face’s Inference Providers documentation notes that HF Inference charges “past the free-tier credits” and describes billing mechanics.  
Source:  
https://huggingface.co/docs/inference-providers/en/pricing

Because the free tier is credit-based rather than RPM/TPM-based, your “limit” depends on the models you pick and the hardware they route to. For “frontier testing”, the free credit is usually enough for smoke tests, not repeated benchmarking.

---

## Vercel AI Gateway ($5/month free credit)

Vercel’s pricing documentation for AI Gateway states that every Vercel team account includes **$5 of free usage per month**, credited every 30 days after your first AI Gateway request, and usable across their model catalog.  
Source:  
https://vercel.com/docs/ai-gateway/pricing  
(See also the AI Gateway FAQ page.)  
https://vercel.com/ai-gateway

Important condition: Vercel notes that after you make your first payment you are considered a paid customer and will no longer receive the free credits.  
Source:  
https://vercel.com/ai-gateway

---

## Google Gemini API (AI Studio free tier)

Google’s Gemini API documentation explains that rate limits exist, are defined per model, and are viewable in the developer console; the public docs I retrieved did not reliably expose a full numeric table for the free tier.  
Source:  
https://ai.google.dev/gemini-api/docs/rate-limits

For practical testing, the most robust workflow is to record the model ID (e.g., *Flash-Lite class*), then capture the exact RPM/TPM/RPD values shown in your AI Studio “limits” view at the time of testing, since those are the operative caps for your account and region.

---

## NVIDIA API Catalog credits (trial)

NVIDIA staff posts on the NVIDIA Developer Forums describe the API catalog as a trial experience limited to **5000 free API credits**, with **1000 credits upon sign-up**, and a mechanism to request more (often involving business email verification and a trial).  
Source:  
https://forums.developer.nvidia.com/t/nim-api-credits/305703

---

## Hyperbolic (promo credit + per-model RPM limits)

Hyperbolic’s pricing documentation states that users can receive **$1 of promotional credits** for verifying a phone number, and provides example per-model RPM limits by user tier for some large models.  
Source:  
https://docs.hyperbolic.xyz/docs/hyperbolic-pricing

---

## Fireworks AI (promo credit)

Fireworks’ documentation notes that new users receive free credits and includes FAQ text referencing “finishing my $1 credit,” implying an initial small promo balance.  
Sources:  
https://docs.fireworks.ai/faq-new/billing-pricing/how-much-does-fireworks-cost  
https://docs.fireworks.ai/faq-new/billing-pricing/what-happens-when-i-finish-my-1-dollar-credit

---

## OpenAI API (generally not free)

OpenAI’s Help Center documentation describes prepaid billing and states that the **minimum purchase is $5**, which is inconsistent with an “always-free API tier” framing.  
Sources:  
https://help.openai.com/en/articles/8264644-how-can-i-set-up-prepaid-billing  
https://help.openai.com/en/articles/8264778-what-is-prepaid-billing

---

## Practical benchmarking advice (brief)

When your goal is “frontier testing” rather than casual prototyping, always log the exact model identifier, context window, and any rate-limit headers or quota errors you encounter. Free tiers are valuable, but they are also elastic and policy-driven, and you want your experiments to be reproducible.


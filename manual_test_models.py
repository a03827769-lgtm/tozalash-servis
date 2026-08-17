import asyncio
import os
import google.generativeai as genai


async def test_models():
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    # Faqat Google AI Studio da tasdiqlangan va barqaror modellar
    models_to_test = ["gemini-2.5-flash", "gemini-2.5-pro"]

    for m in models_to_test:
        print(f"Testing {m}...")
        try:
            model = genai.GenerativeModel(m)
            response = await model.generate_content_async("Hello")
            print(f"✅ {m} WORKS! Response: {response.text}")
        except Exception as e:
            print(f"❌ {m} FAILED: {e}")


if __name__ == "__main__":
    asyncio.run(test_models())

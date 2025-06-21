import requests
from django.conf import settings

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


@api_view(["POST"])
def chat_proxy(request):
    user_message = request.data.get("message")
    client_id = request.data.get("client_id", "anonymous")
    company_info = request.data.get("system_prompt", "You are a helpful assistant.")

    if not user_message:
        return Response({"error": "Message is required."}, status=status.HTTP_400_BAD_REQUEST)

    openrouter_headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": request.META.get("HTTP_ORIGIN", ""),
        "X-Title": "AI Chatbox",
    }

    openrouter_payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": company_info},
            {"role": "user", "content": f"{user_message}."},
        ],
    }

    try:
        router_res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=openrouter_headers,
            json=openrouter_payload,
            timeout=30,
        )
        router_res.raise_for_status()
        ai_response = router_res.json().get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        return Response({"error": "OpenRouter call failed", "details": str(e)}, status=500)

    supabase_headers = {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    try:
        for sender, msg in [("user", user_message), ("ai", ai_response)]:
            requests.post(
                f"{settings.SUPABASE_URL}/rest/v1/messages",
                headers=supabase_headers,
                json={"client_id": client_id, "sender": sender, "message": msg},
                timeout=10
            )
    except Exception as e:
        print("Failed to store in Supabase:", e)

    return Response({"reply": ai_response})

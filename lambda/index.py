# lambda/index.py
import json
import os
import re
import urllib.request
import urllib.error

# 外部 LLM API の URL（ngrokなど）
LLM_API_URL = os.environ.get("LLM_API_URL", "https://33b8-34-127-41-49.ngrok-free.app")

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))

        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])

        print("Processing message:", message)

        # プロンプトを構築
        full_prompt = build_prompt(conversation_history, message)

        payload = {
            "prompt": full_prompt,
            "max_new_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.9,
            "do_sample": True
        }

        print("Calling external LLM API with payload:", json.dumps(payload))

        # POSTリクエスト
        request_url = f"{LLM_API_URL.rstrip('/')}/generate"
        req = urllib.request.Request(
            request_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req) as response:
            response_body = response.read().decode('utf-8')
            result = json.loads(response_body)

        print("LLM API response:", json.dumps(result))

        # 結果を抽出
        assistant_response = result.get("generated_text", "").strip()

        # 会話履歴に追加
        conversation_history.append({"role": "user", "content": message})
        conversation_history.append({"role": "assistant", "content": assistant_response})

        # 成功レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": conversation_history
            })
        }

    except (urllib.error.HTTPError, urllib.error.URLError, Exception) as error:
        print("Error:", str(error))
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }

def build_prompt(conversation_history, latest_message):
    """
    会話履歴と最新メッセージを結合してプロンプトとして構築する
    """
    prompt = ""
    for msg in conversation_history:
        role = msg["role"]
        content = msg["content"]
        prompt += f"{role.capitalize()}: {content}\n"
    prompt += f"User: {latest_message}\nAssistant:"
    return prompt

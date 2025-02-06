curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=AIzaSyBTNVkzjKD3sUNVUMlp_tcXWQMO-FpfrSo" \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{
    "contents": [
      {
        "parts":[{"text": "Hello, how are you?"}]
      }
    ]
  }'

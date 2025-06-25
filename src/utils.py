from typing import Dict, Any, List

import httpx
from src import config, logging
from src.database import save_message, get_or_create_user, get_recent_messages

logger = logging.getLogger(__name__)

async def handle_incoming_message(
    message: Dict[str, Any], contacts: List[Dict[str, Any]]
) -> None:
    """Handle an incoming message based on type and content."""
    try:
        message_type = message.get("type")
        from_number = message.get("from")

        # Get sender information
        sender_name = "User"
        if contacts:
            profile = contacts[0].get("profile", {})
            if profile.get("name"):
                sender_name = profile.get("name")

        logger.info(f"Received {message_type} from {sender_name} ({from_number})")

        # Get or create user
        user_id = await get_or_create_user(
            from_number=from_number, sender_name=sender_name
        )

        if message_type == "text":
            text_body = message.get("text", {}).get("body", "")
            # Save incoming message
            await save_message(user_id, from_number, text_body, "user")

            # Get recent chat history
            recent_messages = await get_recent_messages(from_number)

            # Format chat history for OpenAI
            chat_history = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in recent_messages
            ]
            # Append current message if not already in history
            if not chat_history or chat_history[-1]["content"] != text_body:
                chat_history.append({"role": "user", "content": text_body})

            # Call OpenAI with chat history
            completion = await config.async_client.responses.create(
                model="gpt-4o-mini",
                input=chat_history,
                tools=[
                    {
                        "type": "file_search",
                        "vector_store_ids": [config.VECTOR_STORE_ID],
                        "max_num_results": 20,
                    },
                    {"type": "web_search_preview"},
                ],
            )

            # Save the AI response
            await save_message(
                user_id, from_number, completion.output_text, "assistant"
            )

            # Send the response to the user
            await send_text_message(from_number, completion.output_text)

        elif message_type in ["image", "document"]:
            logger.info(f"Received {message_type} from {sender_name} ({from_number})")
            message_text = f"Thanks for the {message_type}! We've received it."
            await save_message(user_id, from_number, f"{message_type} received", "incoming")
            await save_message(user_id, from_number, message_text, "assistant")
            await send_text_message(from_number, message_text)

        else:
            logger.info(
                f"Received {message_type} from {sender_name} ({from_number})"
            )
            message_text = f"We received your {message_type}. Thank you!"
            await save_message(
                user_id, from_number, f"{message_type} received", "incoming"
            )
            await save_message(user_id, from_number, message_text, "assistant")
            await send_text_message(from_number, message_text)

    except Exception as e:
        logger.error(f"Error handling message: {e}")

async def process_message(data: Dict[str, Any]) -> None:
    """Process incoming messages from WhatsApp and implement business logic."""
    try:
        if data.get("object") == "whatsapp_business_account":
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    if change.get("field") == "messages":
                        for message in change["value"].get("messages", []):
                            contacts = change["value"].get("contacts", [])
                            await handle_incoming_message(message, contacts)
    except Exception as e:
        logger.error(f"Error processing message: {e}")

async def send_text_message(to: str, text: str) -> None:
    """Send a text message to a WhatsApp user."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    result = await send_whatsapp_message(payload)
    if result.get("error"):
        logger.error(f"Failed to send message to {to}: {result['error']}")
    else:
        logger.info(f"Message sent to {to}: {result}")

async def send_whatsapp_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Send a message to WhatsApp via Meta Cloud API."""
    url = f"{config.WHATSAPP_API_URL}/{config.PHONE_NUMBER_ID}/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.WHATSAPP_TOKEN}",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=message, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error when sending message: {e.response.text}")
            return {"error": e.response.text}
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {"error": str(e)}

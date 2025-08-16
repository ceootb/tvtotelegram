from flask import Flask, request, jsonify
import requests
import os
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Discord webhook URL - replace with your actual webhook URL
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL',
                                     'https://discord.com/api/webhooks/1404747703153328249/pu_5psfq3N2N2gIZQaTWv3LqFlb4sVIIlZoxKPvqT_Ta1W7m4tBUrU5bXeNdzDibZeaX')

# Session for connection pooling and better performance
session = requests.Session()
session.headers.update({
    'Content-Type': 'application/json',
    'User-Agent': 'TradingView-Bot/1.0'
})


def send_to_discord(message_content, embed_data=None):
    """
    Send message to Discord with error handling and retries
    """
    try:
        payload = {
            "content": message_content,
            "username": "TradingView Signal Bot",
            "avatar_url": "https://cdn.discordapp.com/attachments/your-avatar-url.png"  # Optional: custom avatar
        }

        # Add embed if provided
        if embed_data:
            payload["embeds"] = [embed_data]

        response = session.post(
            DISCORD_WEBHOOK_URL,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        logger.info("Message sent to Discord successfully")
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send message to Discord: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


def create_signal_embed(signal, ticker, price, waktu):
    """
    Create a rich embed for Discord with better formatting
    """
    # Determine color based on signal
    color = 0x00ff00 if signal.upper() in ['BUY', 'LONG'] else 0xff0000  # Green for buy, Red for sell

    embed = {
        "title": "📡 TradingView Signal Alert",
        "color": color,
        "timestamp": datetime.utcnow().isoformat(),
        "fields": [
            {
                "name": "📈 Trading Pair",
                "value": f"**{ticker}**",
                "inline": True
            },
            {
                "name": "📊 Signal",
                "value": f"**{signal.upper()}**",
                "inline": True
            },
            {
                "name": "💰 Entry Price",
                "value": f"**{price}**",
                "inline": True
            },
            {
                "name": "🕒 Signal Time",
                "value": f"{waktu}",
                "inline": False
            }
        ],
    }

    return embed


@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Webhook endpoint to receive TradingView signals
    """
    try:
        # Validate request
        if not request.is_json:
            logger.warning("Received non-JSON request")
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()

        # Extract and validate data
        signal = data.get("signal")
        ticker = data.get("ticker", "EUR/USD")
        price = data.get("price")
        waktu = data.get("time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        if not signal:
            logger.warning("Missing required field: signal")
            return jsonify({"error": "Missing required field: signal"}), 400

        # Create simple message for fallback
        simple_message = f"🚨 **{signal.upper()}** signal for **{ticker}** at **{price}** | Time: {waktu}"

        # Create rich embed
        embed = create_signal_embed(signal, ticker, price, waktu)

        # Send to Discord
        success = send_to_discord(simple_message, embed)

        if success:
            logger.info(f"Successfully processed signal: {signal} for {ticker}")
            return jsonify({"status": "success", "message": "Signal sent to Discord"}), 200
        else:
            logger.error("Failed to send signal to Discord")
            return jsonify({"status": "error", "message": "Failed to send to Discord"}), 500

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "TradingView Discord Bot"
    }), 200


@app.route("/test", methods=["POST"])
def test_discord():
    """
    Test endpoint to verify Discord integration
    """
    try:
        test_embed = {
            "title": "🧪 Test Message",
            "description": "Discord webhook integration is working!",
            "color": 0x0099ff,
            "timestamp": datetime.utcnow().isoformat()
        }

        success = send_to_discord("✅ Test message from TradingView Bot", test_embed)

        if success:
            return jsonify({"status": "success", "message": "Test message sent"}), 200
        else:
            return jsonify({"status": "error", "message": "Failed to send test message"}), 500

    except Exception as e:
        logger.error(f"Error in test endpoint: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Validate Discord webhook URL
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    if not webhook_url or webhook_url == 'https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN':
        logger.warning("Discord webhook URL not configured properly!")

    port = int(os.environ.get("PORT", 10000))
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

    logger.info(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
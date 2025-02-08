import boto3
import logging
from enum import Enum

#import utils.tool_use_print_utils as output
#import weather_tool

logging.basicConfig(level=logging.INFO, format="%(message)s")

AWS_REGION = "us-east-1"

def enter_company_name(input_query):
    """
    This function prompts the user to enter the company name and asks the model to list out what the company does.
    """
    import boto3
    from botocore.exceptions import ClientError

    # Create a Bedrock Runtime client in the AWS Region you want to use.
    client = boto3.client("bedrock-runtime", region_name="us-east-1")

    # Set the model ID, e.g., Claude 3 Haiku.
    model_id = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"

    # Start a conversation with the user message.
    user_message = "List out what the company does. Company name: " + input_query
    conversation = [
        {
            "role": "user",
            "content": [{"text": user_message}],
        }
    ]

    try:
        # Send the message to the model, using a basic inference configuration.
        response = client.converse(
            modelId=model_id,
            messages=conversation,
            inferenceConfig={"maxTokens": 512, "temperature": 0.5, "topP": 0.9},
        )

        # Extract and print the response text.
        response_text = response["output"]["message"]["content"][0]["text"]
        print(response_text)

    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        exit(1)

enter_company_name("Tesla")

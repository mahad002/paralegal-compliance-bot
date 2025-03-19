from agents import Agent, Runner, WebSearchTool, trace
import asyncio
from guardrails import jurisdiction_guardrail  # Import our guardrail
import os
from dotenv import load_dotenv
# Define the specialized agents




# Data Collection Agent: Collects necessary information from internet search for Pakistani due diligence.
data_collection_agent = Agent(
    name="Data Collection Agent",
    instructions=(
        "Collect necessary information from internet search relevant to the due diligence process in Pakistan. "
        "Focus on local legal data, company records, and news related to the case."
    ),
    tools=[WebSearchTool(user_location={"type": "approximate", "city": "Islamabad"})],
)

# Risk Assessment Agent: Analyzes the collected data to identify legal, financial, and operational risks.
risk_assessment_agent = Agent(
    name="Risk Assessment Agent",
    instructions=(
        "Analyze the collected data to identify potential legal, financial, and operational risks specific to Pakistan's regulatory environment."
    ),
)

# Reporting Agent: Compiles analyzed data into a structured due diligence report.
reporting_agent = Agent(
    name="Reporting Agent",
    instructions=(
        "Compile the analyzed data into a structured report with findings and recommendations based on the user's situation and relevant Pakistani legal data."
    ),
)

# Orchestration Agent: Coordinates the workflow among the specialized agents.
orchestration_agent = Agent(
    name="Orchestration Agent",
    instructions=(
        "Coordinate the due diligence workflow by first running guardrails, then handing off to Data Collection, "
        "Risk Assessment, and Reporting agents in sequence. Finally, consolidate all outputs into a final report."
    ),
    handoffs=[data_collection_agent, risk_assessment_agent, reporting_agent],
    input_guardrails=[jurisdiction_guardrail],  # Apply our jurisdiction guardrail to user input.
)

# Function to collect user input based on essential due diligence questions.
def get_user_input():
    questions = """
Please provide your responses to the following questions about the due diligence process:

1. What is the scope of your due diligence request?
   Example: "Assess legal compliance of a potential acquisition in the textile industry."

2. Which jurisdictions are relevant to your case? (List the main jurisdictions)
   Example: "Federal laws of Pakistan, Provincial regulations in Punjab."

3. What are your main areas of concern for this due diligence?
   Example: "Compliance with anti-money laundering regulations, adherence to labor laws."

Please provide your responses in a clear format below:
"""
    print(questions)
    user_response = input("Your response: ")
    return user_response

# Function to run the due diligence pipeline using the orchestration agent.
async def run_due_diligence_pipeline(orchestration_agent: Agent, user_input: str):
    """
    Run the due diligence pipeline with the orchestration agent.

    Args:
        orchestration_agent: The orchestration agent coordinating the workflow.
        user_input: User's responses to the due diligence questions.
        
    Returns:
        The final output from the pipeline.
    """
    with trace("PARALEGAL WORKFLOW"):
        try:
            result = await Runner.run(orchestration_agent, input=user_input)
            return result.final_output, False  # Return output and flag indicating no guardrail violation
        except Exception as e:
            error_message = str(e)
            if "guardrail" in error_message.lower() or "tripwire" in error_message.lower():
                # Extract the reasoning if available in the error message
                reasoning = error_message
                return f"GUARDRAIL VIOLATION: This request cannot be processed as it appears to reference jurisdictions outside Pakistan. Please ensure your query only relates to Pakistani law.\n\nDetails: {reasoning}", True
            else:
                # Re-raise if it's not a guardrail error
                raise

# Main function to run the pipeline.
async def main():
    
    
    load_dotenv()  # Load variables from .env file

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Get API key
    
    os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY
    
    
    while True:
        # Get user input as a formatted string.
        user_input_str = get_user_input()
        
        # Pass the input to our due diligence pipeline.
        final_output, guardrail_violated = await run_due_diligence_pipeline(orchestration_agent, user_input_str)
        
        print("\nResult:")
        print(final_output)
        
        # If guardrail was violated, ask if they want to try again
        if guardrail_violated:
            retry = input("\nWould you like to try again with a new query? (yes/no): ").lower()
            if retry != "yes":
                break
        else:
            # If no violation, we're done
            break

if __name__ == "__main__":
    asyncio.run(main())
from pydantic import BaseModel
from agents import (
    Agent,
    GuardrailFunctionOutput,
    input_guardrail,
    Runner,
    RunContextWrapper,
)

# Define the output schema for our Pakistan Jurisdiction Guardrail
class PakistanJurisdictionOutput(BaseModel):
    within_pakistan_jurisdiction: bool
    reasoning: str

# Create the guardrail agent that checks if input strictly relates to Pakistani law
jurisdiction_guardrail_agent = Agent(
    name="Pakistan Jurisdiction Guardrail Agent",
    instructions=(
        "Examine the input text and ensure it only references Pakistani jurisdictions and laws. "
        "If any reference to jurisdictions outside Pakistan is detected, set within_pakistan_jurisdiction to False. "
        "Otherwise, set it to True. Provide reasoning accordingly."
    ),
    output_type=PakistanJurisdictionOutput,
)

# Guardrail function that will be used as an input guardrail in the pipeline
@input_guardrail
async def jurisdiction_guardrail(
    ctx: RunContextWrapper[None], agent: Agent, input: str
) -> GuardrailFunctionOutput:
    result = await Runner.run(jurisdiction_guardrail_agent, input, context=ctx.context)
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=not result.final_output.within_pakistan_jurisdiction,
    )
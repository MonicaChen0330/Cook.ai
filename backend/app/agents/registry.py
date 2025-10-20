# This file acts as a single source of truth for all available agents/tasks.
# The Main Orchestrator dynamically uses this registry to:
# 1. Understand what tasks it can perform.
# 2. Generate a prompt for the analysis node to classify user queries.
# 3. Route classified tasks to the correct handler node.

AGENT_REGISTRY = [
    {
        "task_name": "exam_generation",
        "description": "Generates exam questions of various types (e.g., multiple_choice, short_answer, true_false) based on a document.",
        "handler_node_name": "run_exam_generator",
        "parameters": [
            {
                "name": "question_type",
                "type": "str",
                "description": "The type of question to generate. Supported values: 'multiple_choice', 'short_answer', 'true_false'."
            },
            {
                "name": "quantity",
                "type": "int",
                "description": "The number of questions to generate."
            }
        ]
    },
    # {
    #     "task_name": "summarization",
    #     "description": "Summarizes the provided document into a concise overview.",
    #     "handler_node_name": "run_summarizer",
    #     "parameters": []
    # },
]

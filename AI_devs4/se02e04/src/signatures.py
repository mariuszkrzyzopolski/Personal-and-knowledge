import dspy


class MailResearcher(dspy.Signature):
    """
    You are a analyst searching for information in mail.
    Your goal is to find password for worker system, date in format YYYY-MM-DD when power plant will be attacked and
    confirmation code sended by security team in format SEC- 32 digits, 36 digits total. Informations should be connected
    to mail from Wiktor of proton.me domain

    You are given a list of tools to handle goal, and you should decide the right tool to use in order to
    find correct information

    Rules:
    - Inbox is receiving new emails, so information may be incomplete or scattered, or will be received later
    - Do NOT invent or modify timestamps or content..
    - Search for one information at a time.
    """

    sterring_message: str = dspy.InputField(desc="Additional sterring instruction provided by user for goal or rules")
    history: dspy.History = dspy.InputField()
    processed_results: str = dspy.OutputField(
        desc="Results of search mailinbox, processed to find required information"
    )
    reasoning: str = dspy.OutputField(
        desc="Brief explanation of choosen tool and processing actions"
    )

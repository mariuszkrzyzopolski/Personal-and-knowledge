Lean Hypothesis: We believe that giving option to automate package sending will reduce manual work by ~60%.

Problem: Everything need to be manually filled in current system. There is no option for automate preparing declaration to any details provided by user

In scope: module for transport_docs analysis with AI agent(should handle both text and images) connected to MCP server with custom tools(find route code, calculate fee to match budget, fill package declaration)

Anti-goals: Agent is not handling polish text and documents, declaration is not made exactly to format from [text](../transport_docs/zalacznik-E.md), model is not connected to openrouter

M1 Prove It Works: Can we get declaration for package between Gdańsk and Żarnowiec, with 0 budget that is correct with terms? 

Acceptance is achieved when: User can get declaration for package between Gdańsk and Żarnowiec, with 0 budget that is correct with terms and this data:
Nadawca (identyfikator)	450202122
Punkt nadawczy	Gdańsk
Punkt docelowy	Żarnowiec
Waga	2,8 tony (2800 kg)
Budżet	0 PP (przesyłka ma być darmowa lub finansowana przez System)
Zawartość	kasety z paliwem do reaktora
Uwagi specjalne	brak - nie dodawaj żadnych uwag
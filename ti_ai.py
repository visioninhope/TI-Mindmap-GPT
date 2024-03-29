from langchain.chains.question_answering import load_qa_chain
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.callbacks import get_openai_callback
from langchain_community.vectorstores import FAISS
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings, OpenAI as langchainOAI, OpenAIEmbeddings
import pandas as pd


OPENAI_MODEL = "gpt-4-1106-preview"

# Function to summarize the blog to create a short tweet, it work for both OpenAI and Azure OpenAI
def ai_summarise_tweet(input_text, client, ai_service_provider, selected_language, deployment_name):
    """
    Summarizes a long text using a language model.

    Args:
        input_text (str): The text to summarize.
        client (OpenAI): The OpenAI API client.
        ai_service_provider (str): The name of the AI service provider (OpenAI or Azure OpenAI).
        selected_language (List[str]): The list of languages to use for summarization.
        deployment_name (str): The name of the deployment to use for Azure OpenAI.

    Returns:
        str: The summarized text.

    Raises:
        ValueError: If the input parameters are invalid.

    """
   # Combine the selected languages into a string, or default to "English" if none selected
    if not input_text or not client or not ai_service_provider:
        return "Invalid input parameters."
    
    # Combine the selected languages into a string, or default to "English" if none selected
    language = ", ".join(selected_language) if selected_language else "English"

    system_message = f"You are responsible for creating a short tweet in {language} for a Threat Analyst. Write a tweet summary that contains maximum 250 symbols and will summarize the main topic and the key findings relevant for a threat analyst. You can add an emoji. Add tag #timindmap"

    try:
        # Determine the model based on the service provider
        model = OPENAI_MODEL if ai_service_provider == "OpenAI" else deployment_name
        
        # Make the API call
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": input_text},
            ],
        )
        
        return response.choices[0].message.content
    except Exception as e:
        # Return a more informative error message
        return f"An error occurred while generating the tweet summary: {e}"


# Function to summarize the blog, it work for both OpenAI and Azure OpenAI
def ai_summarise(input_text, client, ai_service_provider, selected_language, deployment_name):
    """Summarizes a long text using a language model.

    Args:
        input_text (str): The text to summarize.
        client (OpenAI): The OpenAI API client.
        ai_service_provider (str): The name of the AI service provider (OpenAI or Azure OpenAI).
        selected_language (List[str]): The list of languages to use for summarization.
        deployment_name (str): The name of the deployment to use for Azure OpenAI.

    Returns:
        str: The summarized text.

    Raises:
        ValueError: If the input parameters are invalid.

    """
    # Validate input parameters
    if not input_text or not client or not ai_service_provider:
        return "Invalid input parameters."
    
    # Combine the selected languages into a string, or default to "English" if none selected
    language = ", ".join(selected_language) if selected_language else "English"
    
    # Prepare the system message
    system_message = f"You are responsible for summarizing in {language} a threat report for a Threat Analyst. Write a paragraph that will summarize the main topic, the key findings, and all the detailed information relevant for a threat analyst such as detection opportunity iocs and TTPs. Use the title and add an emoji. Do not generate a bullet points list but rather multiple paragraphs."
    
    try:
        # Determine the model based on the service provider
        model = OPENAI_MODEL if ai_service_provider == "OpenAI" else deployment_name
        
        # Make the API call
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": input_text},
            ],
        )
        
        return response.choices[0].message.content
    except Exception as e:
        # Return a more informative error message
        return f"An error occurred while generating the summary: {e}"


# Function to check if content is related to cybersecurity
def ai_check_content_relevance(input_text, client, ai_service_provider, deployment_name):
    """
    Determines if the input text is related to cybersecurity.

    Args:
        input_text (str): The input text to evaluate.
        client (OpenAI): The OpenAI API client.
        ai_service_provider (str): The name of the AI service provider (OpenAI or Azure OpenAI).
        deployment_name (str): The name of the deployment to use for Azure OpenAI.

    Returns:
        str: A message indicating whether the input text is related to cybersecurity or an error message.

    Raises:
        ValueError: If the input parameters are invalid.

    """
    # Validate input parameters
    if not input_text or not client or not ai_service_provider:
        return "Invalid input parameters."
    
    # Prepare the prompt
    prompt = "Determine if the following text is related to cybersecurity: \n" + input_text
    try:
        # Determine the model based on the service provider
        model = OPENAI_MODEL if ai_service_provider == "OpenAI" else deployment_name
        
        # Make the API call
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": prompt}]
        )
        
        return response.choices[0].message.content
    except Exception as e:
        # Return a more informative error message
        return f"An error occurred while checking content relevance: {e}"


def ai_run_models(input_text, client, selected_language, deployment_name, service_selection):
    """
    Runs the AI models to generate a summary, mindmap, and tweet.

    Args:
        input_text (str): The input text to process.
        client (OpenAI): The OpenAI API client.
        selected_language (List[str]): The list of languages to use for processing.
        deployment_name (str): The name of the deployment to use for Azure OpenAI.
        service_selection (str): The name of the AI service to use (OpenAI or Azure OpenAI).

    Returns:
        str: The output of the AI models.

    Raises:
        ValueError: If the input parameters are invalid.

    """
     # Validate input parameters
    if not input_text or not client or not service_selection:
        return "Invalid input parameters."
    
    # Combine the selected languages into a string, or default to "English" if none selected
    language = ", ".join(selected_language) if selected_language else "English"
    # Define the SYSTEM prompt with guidelines for creating the mindmap
    system_prompt = (
        f"You are tasked with creating an in-depth mindmap in {language} language designed specifically for a threat analyst. "
        "This mindmap aims to visually organize key findings and crucial highlights from the text. Please adhere to the following guidelines in English but apply the approach to {language}: \n"
        "1. Avoid using hyphens in the text, as they cause errors in the Mermaid.js code. \n"
        "2. Limit the number of primary nodes branching from the main node to four. These primary nodes should encapsulate the top four main themes. Add detailed sub-nodes to elaborate on these themes. \n"
        "3. Incorporate icons where suitable to enhance readability and comprehension. \n"
        "4. You MUST use single parentheses around each node to give them a rounded shape. \n"
        "5. Avoid using icons and emojis. \n "
        "6. Do not insert spaces after the text of each line and do not use parentheses or special characters for the names of the chart fields. \n "
        "7. Start mermaid code with word mindmap, don't use anythong else in first line. \n "
        "8. Don't write ``` as the first and last line. \n"
        "9. Avoid using a line with style root. \n"
        "10. Avoid closing with any comment starting with #. \n"
        "11. Do not use theme as the second line; the second line must start with root syntax. \n"
        "12. Special characters need to be escaped or avoided, like brackets in domain. Example: not use mail[.]kz but use mail.kz. \n"
        "13. When encapsulating text within a line, avoid using additional parentheses as they can introduce ambiguity in Mermaid syntax. Instead, use dashes to enclose your text. \n"
        "14. Instead of using the following approach (Indicators of compromise (IOC) provided), use this: (Indicators of compromise - IOC - provided). \n"
    )
    # Define the USER prompt
    user_prompt = (
        "Title:  Threat Report Summary: Kazakhstan-associated YoroTrooper disguises origin of attacks as Azerbaijan\n\nThreat actors known as YoroTrooper, presumably originating from Kazakhstan, have been conducting cyber espionage activities, largely focusing on Commonwealth of Independent States (CIS) countries. These actors mask their origins, making their attacks appear to come from Azerbaijan. Several tactics, techniques, and procedures (TTPs) were used, including using VPN exit points in Azerbaijan and spear phishing via credential-harvesting sites. They have infiltrated websites and accounts of several government officials between May and August 2023.\n\nThe information supporting that YoroTrooper is likely based in Kazakhstan includes the use of Kazakh currency, fluency in Kazakh and Russian, and the limited targeting of Kazakh entities. Interestingly, YoroTrooper has shown a defensive interest in the website of the Kazakhstani state-owned email service (mail[.]kz), taking precautions to ensure it is not exposed to potential security vulnerabilities. The only Kazakh institution targeted was the government’s Anti-Corruption Agency.\n\nYoroTrooper subtly alters its actions to blur its origin, using various tactics to point to Azerbaijan. In addition to routinely rerouting its operations via Azerbaijan, the threat actors frequently translate Azerbaijani to Russian and draft lures in Russian before converting them to Azerbaijani for their phishing attacks. The addition of Uzbek language in their payloads since June 2023 poses another layer of obfuscation, but is likely a demonstration of the actors' multilingual abilities rather than an attempt to mask as an Uzbek adversary.\n\nIn terms of malware use, YoroTrooper has evolved from relying heavily on commodity malware to also using custom-built malware across platforms such as Python, PowerShell, GoLang, and Rust. There is evidence that this threat actor continues to learn and adapt. There has been successful intrusion into several CIS government entities, indicating possible state-backing or state interests serving as motivation.\n\nInvestigations into YoroTrooper are ongoing to determine the extent of potential state sponsorship and additionally whether there is another motivator or objective, such as financial gain through the sale of state-held information. Protective countermeasures have been highlighted. Various IOCs are listed on GitHub for public access."
    )
    # Define the ASSISTANT prompt
    assistant_prompt = (
        "mindmap\nroot(YoroTrooper Threat Analysis)\n    (Origin and Target)\n      ::icon(fa fa-crosshairs)\n      (Likely originates from Kazakhstan)\n      (Mainly targets CIS countries)\n      (Attempts to make attacks appear from Azerbaijan)\n    (TTPs)\n      ::icon(fa fa-tactics)\n      (Uses VPN exit points in Azerbaijan)\n      (Spear phishing via credential-harvesting sites)\n      (Infiltrates websites and accounts of government officials)\n      (Subtly alters actions to blur origin)\n    (Language Proficiency)\n      ::icon(fa fa-language)\n      (Fluency in Kazakh and Russian)\n      (Translates Azerbaijani to Russian for phishing attacks)\n      (Uses Uzbek language in payloads)\n    (Malware Use)\n      ::icon(fa fa-bug)\n      (Evolved from commodity malware to custom-built malware)\n      (Uses Python, PowerShell, GoLang, and Rust platforms)\n    (Investigations and Countermeasures)\n      ::icon(fa fa-search)\n      (Ongoing investigations into potential state sponsorship)\n      (Protective countermeasures highlighted)\n      (IOCs listed on GitHub for public access)"
    )
    try:
        # Determine the model based on the service provider
        model = OPENAI_MODEL if service_selection == "OpenAI" else deployment_name
        
        # Make the API call
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": assistant_prompt},
                {"role": "user", "content": input_text},
            ],
        )
        
        return response.choices[0].message.content
    except Exception as e:
        # Return a more informative error message
        return f"An error occurred while generating the mindmap: {e}"


def ai_run_models_tweet(input_text, client, selected_language, deployment_name,service_selection):
    """
    Creates a mindmap in the specified languages using the specified OpenAI API client.

    Args:
        input_text (str): The input text to use for generating the mindmap.
        client (OpenAI): The OpenAI API client to use for making requests.
        selected_language (List[str]): The list of languages to use for generating the mindmap.
        deployment_name (str): The name of the deployment to use for Azure OpenAI.
        service_selection (str): The name of the AI service provider (OpenAI or Azure OpenAI).

    Returns:
        str: The generated mindmap in the specified languages or an error message.

    Raises:
        ValueError: If the input parameters are invalid.

    """
    # Combine the selected languages into a string, or default to "English" if none selected
    language = ", ".join(selected_language) if selected_language else "English"

    system_prompt = f"You are tasked with creating an mindmap in {language} language designed specifically for a threat analyst. This mindmap aims to visually organize 3 or 4 brances or key findings and crucial highlights from the text, considering each branch cannot have more than 2 subbranches. Please adhere to the following guidelines in english but apply approach to {language}: \n1. Avoid using hyphens in the text, as they cause errors in the Mermaid.js code 2. Limit the number of primary nodes branching from the main node to four. These primary nodes should encapsulate the top four main themes. Add detailed sub-nodes to elaborate on these themes \n3. Incorporate icons where suitable to enhance readability and comprehension\n4. Use single parentheses around each node to give them a rounded shape.\n5. avoid using icons and emoji\n6. Do not insert spaces after the text of each line and do not use parentheses or special characters for the names of the chart fields.\n7 Start mermaid code with 'mindmap', not use as first line \n8 Don't write ``` as last line. \n9 Avoid use line with style root. \n10 Avoid close with any comment starting with # . \n11 not use theme as second line, second line must start with root syntax. \n12 special characters need to be escaped or avoided, like brackets in domain. Example: not use mail[.]kz but use mail.kz \n13 When encapsulating text within a line, avoid using additional parentheses as they can introduce ambiguity in Mermaid syntax. Instead, use dashes to enclose your text \n14 Instead of using following approach (Indicators of compromise (IOC) provided) use this: (Indicators of compromise - IOC - provided)."
    system_prompt_user = "Title:  Threat Report Summary: Kazakhstan-associated YoroTrooper disguises origin of attacks as Azerbaijan\n\nThreat actors known as YoroTrooper, presumably originating from Kazakhstan, have been conducting cyber espionage activities, largely focusing on Commonwealth of Independent States (CIS) countries. These actors mask their origins, making their attacks appear to come from Azerbaijan. Several tactics, techniques, and procedures (TTPs) were used, including using VPN exit points in Azerbaijan and spear phishing via credential-harvesting sites. They have infiltrated websites and accounts of several government officials between May and August 2023.\n\nThe information supporting that YoroTrooper is likely based in Kazakhstan includes the use of Kazakh currency, fluency in Kazakh and Russian, and the limited targeting of Kazakh entities. Interestingly, YoroTrooper has shown a defensive interest in the website of the Kazakhstani state-owned email service (mail[.]kz), taking precautions to ensure it is not exposed to potential security vulnerabilities. The only Kazakh institution targeted was the government’s Anti-Corruption Agency.\n\nYoroTrooper subtly alters its actions to blur its origin, using various tactics to point to Azerbaijan. In addition to routinely rerouting its operations via Azerbaijan, the threat actors frequently translate Azerbaijani to Russian and draft lures in Russian before converting them to Azerbaijani for their phishing attacks. The addition of Uzbek language in their payloads since June 2023 poses another layer of obfuscation, but is likely a demonstration of the actors' multilingual abilities rather than an attempt to mask as an Uzbek adversary.\n\nIn terms of malware use, YoroTrooper has evolved from relying heavily on commodity malware to also using custom-built malware across platforms such as Python, PowerShell, GoLang, and Rust. There is evidence that this threat actor continues to learn and adapt. There has been successful intrusion into several CIS government entities, indicating possible state-backing or state interests serving as motivation.\n\nInvestigations into YoroTrooper are ongoing to determine the extent of potential state sponsorship and additionally whether there is another motivator or objective, such as financial gain through the sale of state-held information. Protective countermeasures have been highlighted. Various IOCs are listed on GitHub for public access."
    system_prompt_asistant = "mindmap\nroot(YoroTrooper Threat Analysis)\n    (Origin and Disguise)\n       ::icon(fa fa-crosshairs)\n      (Presumed origin: Kazakhstan)\n      (Disguises attacks as from Azerbaijan)\n    (TTPs and Language Use)\n      ::icon(fa fa-tactics)\n      (Uses VPNs and spear phishing)\n      (Languages: Kazakh, Russian, Azerbaijani, Uzbek)\n    (Malware Evolution)\n      ::icon(fa fa-bug)\n      (From commodity to custom malware)\n      (Platforms: Python, PowerShell, GoLang, Rust)\n"


    # Determine the model based on the service provider
    model = "gpt-4-1106-preview" if service_selection == "OpenAI" else deployment_name

    # Prepare the messages for the API call
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": system_prompt_user},
        {"role": "assistant", "content": system_prompt_asistant},
        {"role": "user", "content": input_text},
    ]

    try:
        # Make the API call
        response = client.chat.completions.create(
            model=model,
            messages=messages,
        )
        return response.choices[0].message.content
    except Exception as e:
        # Return a more informative error message
        return f"An error occurred while generating the mindmap: {e}"



def ai_extract_iocs(input_text, client, service_selection, deployment_name):
    """
    Extract Indicators of Compromise (IOCs) from unstructured text using OpenAI's API.

    Args:
        input_text (str): The unstructured text to extract IOCs from.
        client (OpenAIAPI): The OpenAI API client to use for making requests.
        service_selection (str): The name of the OpenAI service to use for completions.
        deployment_name (str): The name of the Azure OpenAI deployment to use for completions.

    Returns:
        pd.DataFrame: A pandas DataFrame containing the extracted IOCs.

    Raises:
        ValueError: If the input text is empty or the OpenAI API client is not provided.
    """

    # Prepare the system message
    prompt = (
        "You are tasked with extracting IOCs from the following blog post for a threat analyst. "
        "Provide a structured, table-like format, with rows separated by newlines and columns by commas "
        "with the following rows: Indicator, Type, Description. Extract indicators just if you are able to find them "
        "in the blog post provided. With reference to IP addresses, URLs, and domains, remove square brackets. "
        "Examples: tech[.]micrsofts[.]com will be tech.micrsofts.com and 27.102.113.93"
    )

    # Determine the model based on the service provider
    model = OPENAI_MODEL if service_selection == "OpenAI" else deployment_name

    # Make the API call
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": prompt + "\n\n" + input_text}],
    )

    # Extract and return the response content
    try:
        response_content = response.choices[0].message.content
        # Parse the response content into a DataFrame
        data = [line.split(",") for line in response_content.strip().split("\n")]
        max_columns = max(len(row) for row in data)
        standardized_data = [row + [''] * (max_columns - len(row)) for row in data]
        df = pd.DataFrame(standardized_data[1:], columns=standardized_data[0])
        return df
    except Exception as e:
        return f"Failed to extract and parse IOCs: {e}"


def ai_ttp(text, client,service_selection, deployment_name, input_text):
    """
    This function is used to extract TTPs from a given text using the OpenAI API.

    Args:
        text (str): The text from which the TTPs will be extracted.
        client (OpenAI API client): The OpenAI API client used to make requests.
        service_selection (str): The service selection, either "OpenAI" or "Azure OpenAI".
        deployment_name (str): The name of the Azure OpenAI deployment.
        input_text (str): The input text for the API call.

    Returns:
        str: The response from the API call.
    """
  # Define the SYSTEM prompt with guidelines for creating the mindmap
    system_prompt_ttp = (
            "You are an AI assistant expert in cybersecurity, threat intelligence, and Mitre attack, assisting Infosec professionals in understanding cyber attacks."
    )
        # Define the USER prompt
    user_prompt_ttp = (
            f"With reference to ATT&CK Matrix for Enterprise extract TTPs (tactics and techniques) from text at the end of following prompt. \n"
            "For each techniques try to provide techniqueID, tactic, comment if you can get relevant content from text, producing a table with following columns: technique, technique ID, tactic, comment. \n"
            "Text to work with: {text}"
        )
  # Determine the model based on the service provider
    model = OPENAI_MODEL if service_selection == "OpenAI" else deployment_name

    # Prepare the messages for the API call
    messages = [
        {"role": "system", "content": system_prompt_ttp},
        {"role": "user", "content": user_prompt_ttp},
        {"role": "user", "content": input_text},
    ]

    # Make the API call
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )

    # Return the response content
    return response.choices[0].message.content



def ai_ttp_list(text, ttptable, client, service_selection, deployment_name):
    """
    This function takes as input a text, a table of TTPs, a client, a service selection, and a deployment name.
    The function makes an API call to the specified client using the specified service selection and deployment name,
    and returns the response content.

    Args:
        text (str): The text to process.
        ttptable (str): The table of TTPs.
        client: The client to use for the API call.
        service_selection (str): The service selection to use for the API call.
        deployment_name (str): The deployment name to use for the API call.

    Returns:
        str: The response content from the API call.
    """
    # Define the SYSTEM prompt
    system_prompt_ttp_list = (
        "You are an AI assistant expert in cybersecurity, threat intelligence, and Mitre attack, assisting Infosec professionals in understanding cyber attacks."
    )
    # Define the USER prompt
    user_prompt_ttp_list = (
        f"Based on {text} and {ttptable} provide a list of TTPs order by execution time, Each line must include only Tactic and Subtactic, IDs between brackets after subtactic. \n"
        "The Enterprise tactics names as defined by the MITRE ATT&CK framework are: Reconnaissance, Resource Development, Initial Access, Execution, Persistence, Privilege Escalation, Defense Evasion, Credential Access, Discovery, Lateral Movement, Collection, Command and Control, Exfiltration, Impact"
    )
    # Determine the model based on the service provider
    model = OPENAI_MODEL if service_selection == "OpenAI" else deployment_name

    # Prepare the messages for the API call
    messages = [
        {"role": "system", "content": system_prompt_ttp_list},
        {"role": "user", "content": user_prompt_ttp_list},
    ]

    # Make the API call
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )

    # Return the response content
    return response.choices[0].message.content




def ai_ttp_graph_timeline(text, client, service_selection, deployment_name, input_text):
  """
    Generate a Mermaid.js timeline graph that illustrates the stages of a cyber attack based on the provided timeline text.

    Args:
        text (str): The timeline text that contains the TTPs of the cyber attack.
        client: The OpenAI API client.
        service_selection (str): The AI service selection (OpenAI or Azure OpenAI).
        deployment_name (str): The Azure OpenAI deployment name.
        input_text (str): The input text for the AI service.

    Returns:
        The generated Mermaid.js timeline graph as a string.
    """
  # Define the USER prompt
  user_prompt_ttp_graph_timeline = (
          f"Write a Mermaid.js timeline graph that illustrates the stages of a cyber attack whose TTPs timeline is as follows: {text} .\n"
          "As an example condider the Lazarus Group's operation named Operation Blacksmith, whose Tactics, Techniques, and Procedures (TTPs) timeline is as follows: {ttps_timeline}, and related meirmad.js code is: {mermaid_timeline}. \n"
          "Use the Enterprise tactics names as defined by the MITRE ATT&CK framework are: Reconnaissance, Resource Development, Initial Access, Execution, Persistence, Privilege Escalation, Defense Evasion, Credential Access, Discovery, Lateral Movement, Collection, Command and Control, Exfiltration, Impact"
          "Use the following guidalines to generate code: \n"
          "1. Use keyword timeline to start the graph definition, timeline must be first word in the output, don't use anything else. \n"
          "2. title: This keyword is followed by the title of the timeline graph \n"
          "3. Each timeline step is defined on a separate line and starts with a description of the step. The description should be concise and informative, summarizing the key actions or events of the step. \n"
          "4 The description is followed by a colon (:) and then the step details \n"
          "5. The step details can include any additional information about the step, such as the specific tools or techniques used. \n"
          "6. Optionally, the step details can include a reference to a malleable threat technique ID using square brackets. \n"
          "7. Avoid provide days after TTP ID. \n"
          "8. Provide just mermaid.js code without any other text. \n"
          "9. Start code with timeline- \n"
          "10. Don't use any bracket at the benning and the end of your output. \n"
          "11. When encapsulating text within a line, avoid using additional parentheses as they can introduce ambiguity in Mermaid syntax. Instead, use dashes to enclose your text. \n"
          "12. Don't write ``` as the first and last line."
    )
  if service_selection == "OpenAI":
        # OpenAI API call
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "user", "content": user_prompt_ttp_graph_timeline},
                {"role": "user", "content": input_text},
            ],
        )
        return response.choices[0].message.content
  elif service_selection == "Azure OpenAI":
        # Azure OpenAI API call
        response = client.chat.completions.create(
            model = deployment_name,
            messages=[
                {"role": "user", "content": user_prompt_ttp_graph_timeline},
                {"role": "user", "content": input_text},
            ],
        )
        return response.choices[0].message.content



def ai_process_text(text, service_selection, azure_api_key, azure_endpoint, embedding_deployment_name, openai_api_key):
    """
    Processes the input text using various NLP techniques and returns a FAISS knowledge base.

    Args:
        text (str): The input text to be processed.
        service_selection (str): The AI service to be used for processing the text. Can be either "OpenAI" or "Azure OpenAI".
        azure_api_key (str): The API key for the Azure Cognitive Services endpoint. Required if using "Azure OpenAI".
        azure_endpoint (str): The endpoint URL for the Azure Cognitive Services endpoint. Required if using "Azure OpenAI".
        embedding_deployment_name (str): The name of the Azure Machine Learning deployment that contains the text embedding model. Required if using "Azure OpenAI".
        openai_api_key (str): The API key for the OpenAI API. Required if using "OpenAI".

    Returns:
        Optional[FAISS]: The FAISS knowledge base containing the processed text embeddings. Returns None if the processing fails.

    Raises:
        ValueError: If the service selection is invalid.
    """
    text_splitter = CharacterTextSplitter(separator="\n", chunk_size=500, chunk_overlap=100, length_function=len)
    chunks = text_splitter.split_text(text)

    embeddings = []
    if chunks:
        if service_selection == "OpenAI":
            embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        elif service_selection == "Azure OpenAI":
            embeddings = AzureOpenAIEmbeddings(deployment=embedding_deployment_name,
                                        model="text-embedding-ada-002",
                                        azure_endpoint=azure_endpoint,
                                        api_key=azure_api_key,
                                        chunk_size=1,
                                        api_version="2024-02-15-preview")
        else:
            raise ValueError("Invalid AI service selection")

        if not embeddings:
            raise ValueError("Embeddings list is empty. Please check the input text and the AI service configuration.")

    #st.write(f"Embeddings after generation: {embeddings}")  

    knowledge_base = None
    if embeddings:
        knowledge_base = FAISS.from_texts(chunks, embeddings)
    return knowledge_base



def ai_get_response(knowledge_base, query, service_selection, azure_api_key, azure_endpoint, deployment_name, openai_api_key):
    """
    Get a response from a knowledge base using a query.

    Args:
        knowledge_base (FAISS): The knowledge base to search.
        query (str): The query to search the knowledge base with.
        service_selection (str): The AI service to use.
        azure_api_key (str): The Azure API key for the Azure OpenAI service.
        azure_endpoint (str): The Azure endpoint URL for the Azure OpenAI service.
        deployment_name (str): The name of the Azure OpenAI deployment.
        openai_api_key (str): The OpenAI API key for the OpenAI service.

    Returns:
        str: The response from the knowledge base.
    """
    docs = knowledge_base.similarity_search(query)

    if service_selection == "OpenAI":
        llm = langchainOAI(openai_api_key=openai_api_key)
    elif service_selection == "Azure OpenAI":
        llm = AzureChatOpenAI(model="gpt-4-32k",
                              deployment_name=deployment_name,
                              api_key=azure_api_key,
                              api_version="2023-07-01-preview",
                              azure_endpoint=azure_endpoint
                     )
    else:
        raise ValueError("Invalid AI service selection")

    chain = load_qa_chain(llm, chain_type="stuff")
    with get_openai_callback() as cost:
        response = chain.invoke(input={"question": query, "input_documents": docs})
    return response["output_text"]



prompt_table = """
| Technique                                | Technique ID | Tactic           | Comment                                                                                                      |
|------------------------------------------|--------------|------------------|--------------------------------------------------------------------------------------------------------------|
| Used CVE-2021-44228 for initial access.   | T1190        | Initial Access   | Used CVE-2021-44228 to exploit publicly exposed servers for initial access.                                  |
| Used commands and scripts for execution.  | T1059        | Execution        | Used commands and scripts (like PowerShell and BAT) to execute different operations.                         |
| Used NineRAT for persistence.             | T1543        | Persistence      | Used NineRAT to set up persistence by creating services using BAT scripts.                                     |
| NineRAT dropper deletes itself for defense evasion. | T1140 | Defense Evasion  | NineRAT has a dropper binary containing two other components, written to disk, and the dropper deletes itself to avoid detection. |
| Used Telegram for command and control.   | T1102        | Command and Control | Used Telegram bots and channels for C2 communications.                                                       |
| Used commands for system information discovery. | T1082 | Discovery        | Used commands like "whoami," "ver," "getmac" for system information discovery.                                |
| Used NineRAT for data collection.         | T1005        | Collection       | NineRAT is used to collect data from the local system.                                                        |
"""
prompt_response = """
{
  "name": "Lazarus Group TTPs",
  "versions": {
    "attack": "14",
    "navigator": "4.9.1",
    "layer": "4.5"
  },
  "domain": "enterprise-attack",
  "description": "TTPs identified in Lazarus Group's Operation Blacksmith",
  "filters": {
    "platforms": ["windows"]
  },
  "sorting": 0,
  "layout": {
    "layout": "side",
    "aggregateFunction": "average",
    "showID": false,
    "showName": true,
    "showAggregateScores": false,
    "countUnscored": false,
    "expandedSubtechniques": "none"
  },
  "hideDisabled": false,
  "techniques": [
    {
      "techniqueID": "T1190",
      "tactic": "initial-access",
      "color": "",
      "comment": "Used CVE-2021-44228 to exploit publicly exposed servers for initial access.",
      "enabled": true,
      "metadata": [],
      "links": [],
      "showSubtechniques": false
    },
    {
      "techniqueID": "T1059",
      "tactic": "execution",
      "color": "",
      "comment": "Used commands and scripts (like PowerShell and BAT) to execute different operations",
      "enabled": true,
      "metadata": [],
      "links": [],
      "showSubtechniques": false
    },
    {
      "techniqueID": "T1543",
      "tactic": "persistence",
      "color": "",
      "comment": "Used NineRAT to set up persistence by creating services using BAT scripts.",
      "enabled": true,
      "metadata": [],
      "links": [],
      "showSubtechniques": false
    },
    {
      "techniqueID": "T1140",
      "tactic": "defense-evasion",
      "color": "",
      "comment": "NineRAT has a dropper binary containing two other components, which are written to disk and the dropper deletes itself to avoid detection.",
      "enabled": true,
      "metadata": [],
      "links": [],
      "showSubtechniques": false
    },
    {
      "techniqueID": "T1102",
      "tactic": "command-and-control",
      "color": "",
      "comment": "Used Telegram bots and channels for C2 communications.",
      "enabled": true,
      "metadata": [],
      "links": [],
      "showSubtechniques": false
    },
    {
      "techniqueID": "T1082",
      "tactic": "discovery",
      "color": "",
      "comment": "Used commands like \"whoami\", \"ver\", \"getmac\" for system information discovery.",
      "enabled": true,
      "metadata": [],
      "links": [],
      "showSubtechniques": false
    },
    {
      "techniqueID": "T1005",
      "tactic": "collection",
      "color": "",
      "comment": "NineRAT is used to collect data from the local system.",
      "enabled": true,
      "metadata": [],
      "links": [],
      "showSubtechniques": false
    }
  ],
  "gradient": {
    "colors": ["#ff6666", "#ffe766", "#8ec843"],
    "minValue": 0,
    "maxValue": 100
  },
  "legendItems": [],
  "metadata": [],
  "links": [],
  "showTacticRowBackground": false,
  "tacticRowBackground": "#dddddd"
}
"""
ttps_timeline = """
1. Initial Access: Exploitation of Remote Services [T1210]
2. Execution: Command and Scripting Interpreter: PowerShell [T1059.001]  
3. Persistence: External Remote Services [T1133]
4. Persistence: Server Software Component: Web Shell [T1505.003]
5. Persistence: Account Creation [T1136]
6. Defense Evasion: Use Alternate Authentication Material [T1550]
7. Defense Evasion: Modify Registry [T1112]
8. Defense Evasion: Indicator Removal on Host: File Deletion [T1070.004]
9. Credential Access: OS Credential Dumping [T1003]
10. Discovery: System Information Discovery [T1082]
11. Collection: Data Staged: Local Data Staging [T1074.001]
12. Command and Control: Remote Access Tools [-]
13. Command and Control: Proxy: Multi-hop Proxy [T1090.003]
14. Command and Control: Application Layer Protocol: Web Protocols [T1071.001]
15. Command and Control: Ingress Tool Transfer [T1105]
16. Impact: Data Encrypted for Impact [T1486]
"""

mermaid_timeline = """
timeline
title Lazarus Group Operation Blacksmith
    Initial Access
    : Exploitation of Remote Services - [T1210]
	Execution
    : Command and Scripting Interpreter - PowerShell - [T1059.001]  
    Persistence
    : External Remote Services - [T1133]
	: Server Software Component - Web Shell - [T1505.003]
	: Account Creation - [T1136]
	Defense Evasion
	: Use Alternate Authentication Material - [T1550]
	: Modify Registry - [T1112]
	: Indicator Removal on Host - File Deletion - [T1070.004]
	Credential Access
    : OS Credential Dumping - [T1003]
    Discovery
    : System Information Discovery - [T1082]
    Collection: Data Staged - Local Data Staging - [T1074.001]
	Command and Control
    : Remote Access Tools - [-]
    : Proxy Multi-hop Proxy - [T1090.003]
    : Application Layer Protocol Web Protocols - [T1071.001]
	: Ingress Tool Transfer - [T1105]
    Impact: Data Encrypted for Impact - [T1486]
"""


################################################################
##UNUSED FUNCTIONS
################################################################
################################################################

"""

def ai_attack_layer(text, client, ttptable,prompt_table, prompt_response,service_selection, deployment_name):
  # Define the SYSTEM prompt
  system_prompt_attack_layer = (
      f"You are tasked with creating an ATT&CK Matrix for Enterprise layer json file with attack version 14, navigator 4.9.1, layer version 4.5 to load a layer in MITRE ATT&CK Navigator. \n"
      "Use {ttptable} as input. Print just json content, avoiding including any additional text in the response. In domain field use enterprise-attack."
  )
  # Define the USER prompt
  user_prompt_attack_layer = (
      f"Title:  Enterprise techniques used by 2015 Ukraine Electric Power Attack, ATT&CK campaign C0028 (v1.0): Table: {prompt_table}"
  )
  # Define the ASSISTANT prompt
  assistant_prompt_attack_layer = (
      f"{prompt_response}"
  )
  if service_selection == "OpenAI":
        # OpenAI API call
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": system_prompt_attack_layer},
                {"role": "user", "content": user_prompt_attack_layer},
                {"role": "assistant", "content": assistant_prompt_attack_layer},
                {"role": "user", "content": input_text},
            ],
        )
        return response.choices[0].message.content
  elif service_selection == "Azure OpenAI":
        # Azure OpenAI API call
        response = client.chat.completions.create(
            model = deployment_name,
            messages=[
                {"role": "system", "content": system_prompt_attack_layer},
                {"role": "user", "content": user_prompt_attack_layer},
                {"role": "assistant", "content": assistant_prompt_attack_layer},
                {"role": "user", "content": input_text},
            ],
        )
        return response.choices[0].message.content
"""




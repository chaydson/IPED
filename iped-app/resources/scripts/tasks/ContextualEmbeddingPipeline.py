from typing import List
from openai import OpenAI

class ContextualEmbeddingPipeline:
    """
    A pipeline that:
      1. Splits document text into overlapping chunks (no LangChain).
      2. (Optionally) generates chunk-specific context via client.chat.completions.create().
      3. Obtains batch embeddings from client.embeddings.create().

    This uses the new 'openai.OpenAI' style, with a custom local base_url if desired.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        chat_model: str,
        embed_model: str,
        chunk_size: int,
        chunk_overlap: int,
    ):
        """
        :param base_url: Your local or remote OpenAI-compatible API base (e.g. "http://localhost:8000/v1")
        :param api_key: API key if required by the service
        :param chat_model: Model name to use for ChatCompletion
        :param embed_model: Model name to use for embeddings
        :param chunk_size: Characters per chunk
        :param chunk_overlap: Overlapping characters between chunks
        """
        # Create an OpenAI client that points to your custom base_url
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )

        self.chat_model = chat_model
        self.embed_model = embed_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> List[str]:
        """
        Splits a text into overlapping chunks of size `chunk_size` with overlap `chunk_overlap`.
        """
        text = text.strip()
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk = text[start:end]
            chunks.append(chunk)
            start += (self.chunk_size - self.chunk_overlap)
        return chunks

    def generate_contextual_chunks(self, chunk_texts: List[str]) -> tuple[list[str], list[str]]:
        """
        For each chunk, call the chat model to produce a short context string, then prepend it.
        Using client.chat.completions.create(...).
        """
        contextual_chunks = []
        summaries = []
        for chunk in chunk_texts:
            messages = [
                {"role": "system", "content": "/no_think\n\nYou are an expert summarizer and analyzer who can help me."},
                {
                    "role": "user",
                    "content": (
                        "Generate a concise and coherent summary from the given chunk of conversation found in WhatsApp app."
                        "Condense the chunk into a well-written summary that captures the main ideas, key points, and insights presented."
                        "Whenever the word “Owner” appears, refer to it in the summary as 'dono do aparelho'."
                        "Prioritize in the summary any details that could aid an investigation, but **do not label or imply that the content could (or could not) investigation-related.**"
                        "Include the date period of the conversation, placing it in the beggining of the summary."
                        "Omit greetings and other casual conversation."
                        "Summary should be UNDER 500 characters and in portuguese pt-BR."
                        f"<chunk>\n{chunk}\n</chunk>\n\n"
                    )
                }
            ]
            
            
            ''' [
                {"role": "system", "content": "/no_think\n\nYou are a helpful assistant following strict instructions."},
                {
                    "role": "user",
                    "content": (
                        f"Here is the chunk of a chat that we want to summarize:\n"
                        f"<chunk>\n{chunk}\n</chunk>\n\n"
                        f"Analyze the chunk and generate an one line summary that captures the core meaning and main points."
                        f"On larger chunks, focus on content that can be relevant for investigation and not on day to day messages as greatings that are irrelevant."
                        f"Answer under 500 characters in portuguese pt-BR." #**ONLY with that core meaning and main points** summary."
                    )
                }
            ]''' 

            '''https://www.reddit.com/r/LocalLLaMA/comments/1ftjbz3/shockingly_good_superintelligent_summarization/
            [
                {"role": "system", "content": "You are a helpful context generator following strict instructions."},
                {
                    "role": "user",
                    "content": (
                        f"Here is the chunk we want to summarize:\n"
                        f"<chunk>\n{chunk}\n</chunk>\n\n"
                        "1.) Analyze the chunk text and generate 5 essential questions that, when answered, capture the main points and core meaning of the text."
                        "2.) When formulating your questions: a. Address the central theme or argument b. Identify key supporting ideas c. Highlight important facts or evidence e. Explore any significant implications or conclusions. "
                        "3.) Answer all of your generated questions one-by-one in detail. "
                    )
                }
            ]'''


            '''
            [
                {"role": "system", "content": "You are a helpful context generator following strict instructions."},
                {
                    "role": "user",
                    "content": (
                        f"Here is the chunk we want to summarize:\n"
                        f"<chunk>\n{chunk}\n</chunk>\n\n"
                        "Please give a short, succinct context. "
                        "Do not make assumptions or inferences. "
                        "Be conservative and factual. "
                        "If something is ambiguous or unclear, leave it as-is. "
                        "Do not over-condense"
                        "Retain important names"
                        "Answer in portuguese pt-BR ONLY with that short context."
                    )
                }
            ]
            '''
            '''[
                {"role": "system", "content": "You are a helpful context generator."},
                {
                    "role": "user",
                    "content": (
                        f"Here is the chunk we want to summarize:\n"
                        f"<chunk>\n{chunk}\n</chunk>\n\n"
                        "Please give a short, succinct context to situate this chunk within an overall "
                        "document. Answer in portuguese pt-BR ONLY with that short context."
                    )
                }
            ]
            '''


            '''messages = [
                {"role": "system", "content": "You are a helpful context generator."},
                {
                    "role": "user",
                    "content": (
                        f"<document>\n{whole_document}\n</document>\n\n"
                        "Here is the chunk we want to situate within the whole document:\n"
                        f"<chunk>\n{chunk}\n</chunk>\n\n"
                        "Please give a short, succinct context to situate this chunk within the overall "
                        "document. Answer in portuguese pt-BR ONLY with that short context."
                    )
                }
            ]'''
            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,

                #max_tokens=500,
                #temperature=0.15
            )
            # The returned object has a 'choices' list, each with a 'message'
            context_str = response.choices[0].message.content.strip()
            print(context_str)
            print('--------------------------------------------------------------------------')
            contextual_chunks.append(f"{context_str}\n\n{chunk}")
            summaries.append(context_str)
        return contextual_chunks, summaries

    def embed_chunks(self, chunks: List[str]) -> List[List[float]]:
        """
        Batch-embed the provided chunks using client.embeddings.create(...)
        Returns a list of embedding vectors (each a list of floats).
        """
        # The new style client supports a single call with all inputs in 'input'

        print(self.embed_model)
        response = self.client.embeddings.create(
            model=self.embed_model,
            input=chunks,
           # dimensions=1024
        )
        print("Chegou aqui")
        # Gather embeddings from response.data, each item is {'index':..., 'embedding':...}
        embeddings = [item.embedding for item in response.data]
        return embeddings


# -----------------------------------------------------------------------------
# Example Usage
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Suppose your local or remote server runs at http://localhost:8000/v1
    pipeline = ContextualEmbeddingPipeline(
        base_url="http://192.168.160.208:11434/v1",
        api_key="teste",
        chat_model="qwen2.5:14b-instruct-8k",    # Example
        embed_model="nomic-embed-text:latest",
        chunk_size=10000,
        chunk_overlap=0
    )

    # Some sample text
    document_text = """Carlos (08h15): Bom dia, pessoal! Tudo bem com vocês?

Fernanda (08h17): Bom dia, Carlos! Tudo ótimo. E aí, como foi seu fim de semana?

Carlos (08h18): Foi tranquilo. Consegui descansar bastante e também coloquei algumas pendências em dia. E o seu?

Fernanda (08h20): Meu fim de semana foi cheio: fiz uma trilha no sábado e no domingo fui visitar minha família. Estou cansada, mas foi bem divertido.

Luana (08h21): Oi, gente! Desculpa interromper, mas vocês chegaram a ver o e-mail sobre a nova política de horários flexíveis?

Carlos (08h23): Bom dia, Luana! Eu vi, sim. Parece que agora a gente pode adiantar ou atrasar uma hora no começo do expediente, desde que a gente cumpra as horas diárias.

Fernanda (08h24): Isso mesmo. Estou pensando em entrar mais cedo, assim consigo sair um pouco antes e fugir do trânsito.

Luana (08h26): Eu prefiro chegar um pouco mais tarde, confesso. Sou mais produtiva depois das 10h. Mas acho que é uma boa alternativa para todo mundo.

Fernanda (08h28): Concordo. Inclusive, vou falar com o RH hoje pra ver se preciso assinar algum termo. Mudando de assunto, alguém já falou com o Rodrigo hoje? Ele me mandou uma mensagem dizendo que estava com algumas dúvidas sobre o projeto.

Carlos (08h30): Ainda não falei com ele. Estava aqui preparando um relatório de status do meu time. Mas posso passar lá na sala dele em alguns minutos.

Luana (08h31): Eu acabei de encontrar com o Rodrigo no corredor. Ele comentou algo sobre uma integração que está dando erro no sistema. Acho que é algo relacionado ao web service do fornecedor.

Fernanda (08h33): Nossa, isso é importante. Esse web service está instável há um tempo, e precisamos resolver logo para não atrasar a entrega final.

Carlos (08h35): Vou tentar dar uma olhada. Se precisar, chamo o pessoal de TI pra ajudar. A gente não pode deixar isso pra última hora.

Fernanda (08h36): Perfeito. Depois me fala o que descobriu. Enquanto isso, vou terminar de revisar as telas do módulo de cadastro.

Luana (08h38): Falando em revisão, recebi um e-mail do pessoal de QA pedindo algumas alterações de layout. Você sabe se isso entra no nosso backlog de desenvolvimento agora ou deixa pra próxima sprint?

Carlos (08h40): Depende da urgência, mas pelo que conversamos na reunião de sexta, acho que esses ajustes de layout podem ficar para a próxima sprint, a menos que sejam críticos.

Fernanda (08h42): Vou verificar o documento de priorização, mas concordo com o Carlos. A gente precisa focar nas funcionalidades principais primeiro, até para cumprir o prazo com o cliente.

Rodrigo (08h44): Oi, gente! Desculpa chegar atrasado na conversa. Fiquei preso ali no suporte técnico tentando entender esse erro do web service.

Luana (08h46): E aí, Rodrigo? Descobriu alguma coisa?

Rodrigo (08h48): Então... Parece que a documentação do fornecedor está desatualizada. Eles mudaram alguns parâmetros na API, mas não avisaram oficialmente. Por isso, estamos recebendo respostas inesperadas.

Carlos (08h50): Poxa, que complicado. Você acha que vamos precisar mudar muita coisa no nosso código?

Rodrigo (08h52): Talvez não muito, mas precisamos atualizar os endpoints e revisar as validações. Já estou anotando tudo para repassar ao time de desenvolvimento.

Fernanda (08h53): Ótimo. Assim que tiver algo consolidado, me envia, por favor. Vou adiantar o contato com o fornecedor para tentar uma posição oficial.

Rodrigo (08h55): Combinado. Vou aproveitar e conferir se isso impacta outras integrações que estamos fazendo.

Carlos (08h57): Boa ideia. Qualquer problema, me avisa. Agora vou terminar meu relatório, que o chefe está pedindo há dias.

Luana (08h59): Falando no chefe… Ele agendou uma reunião de última hora para hoje às 11h. Vocês receberam o convite?

Fernanda (09h01): Recebi sim. Parece que vai ser para alinhar a nova estrutura do time. Talvez a gente ganhe reforços em breve.

Rodrigo (09h03): Tomara! A demanda está pesada. Quanto mais gente, melhor.

Carlos (09h05): Vou ficar de olho no e-mail e me preparar. Depois dessa reunião, acredito que muita coisa vai mudar no cronograma.

Fernanda (09h07): Pois é. E não esqueçam que temos outra reunião com o cliente às 16h. Precisamos ter pelo menos uma definição parcial do que vai ser feito.

Luana (09h08): Verdade. Vou preparar alguns slides para apresentar o status atual. Se alguém tiver algo para adicionar, me mandem até as 15h, por favor.

Rodrigo (09h10): Fechado. Eu envio os pontos sobre a integração também.

Carlos (09h12): Combinadíssimo. E, gente, vamos almoçar onde hoje? Tô pensando em ir naquele restaurante de massas que a Fernanda comentou semana passada.

Fernanda (09h14): Ótima opção! Fica perto e é gostoso. Podemos marcar meio-dia?

Luana (09h15): Por mim, tudo bem. Só precisamos sair pontualmente, porque a reunião com o chefe começa às 11h e costuma atrasar.

Rodrigo (09h17): Tranquilo. Assim que acabar a reunião, a gente vai direto. Vou deixar tudo pronto antes.

Fernanda (09h19): Então, combinado. Meio-dia no saguão principal. Agora vou aproveitar para revisar umas propostas que chegaram do marketing.

Carlos (09h20): Beleza, pessoal. Até mais tarde, então. Se precisarem de mim, estou na mesa ao lado.

Luana (09h21): Valeu, gente! Vou adiantar os slides da reunião e qualquer dúvida eu chamo vocês.

Rodrigo (09h22): Vou continuar aqui no web service. Até já!

Fernanda (09h24): Até já, pessoal! Depois me atualizem sobre qualquer novidade!"""

    # 1) Split into chunks
    raw_chunks = pipeline.chunk_text(document_text)

    # 2) (Optional) Generate context for each chunk
    contextualized_chunks = pipeline.generate_contextual_chunks(document_text, raw_chunks)

    # 3) Embed the (contextualized) chunks in batch
    embeddings_list = pipeline.embed_chunks(contextualized_chunks)

    # Print results
    print(f"Number of chunks: {len(contextualized_chunks)}")
    print(f"Number of embeddings: {len(embeddings_list)}")

    for i, embedding in enumerate(embeddings_list[:2], start=1):
        print(f"\n--- Chunk #{i} ---")
        print("Text:", contextualized_chunks[i-1])
        print(f"Embedding dimension: {len(embedding)}")
        print(f"Sample embedding values: {embedding[:5]}...")
import streamlit as st
import google.generativeai as genai


# Edite este texto para mudar completamente o jeito da Olly conversar.
SYSTEM_PROMPT = """
Você é Olly, uma chatbot brasileira com personalidade forte, esperta e bem-humorada.
Responda sempre em português do Brasil, de forma curta, direta e natural.
Tenha opinião, seja confiante e espirituosa, mas nunca seja grosseira ou ofensiva.
Evite textos longos, listas desnecessárias e frases genéricas de assistente virtual.
Se a pergunta for ambígua, peça uma única clarificação objetiva.
Quando não souber algo, diga isso com honestidade.
""".strip()

SECRET_NAME = "AQ.Ab8RN6JNmAhyGQWouny6QVOZJGv2XyAGedadiyYYp5ZMdXBXpw"
MODEL_NAME = "gemini-2.5-flash"


st.set_page_config(
    page_title="Olly — sua chatbot",
    page_icon="💬",
    layout="centered",
)

st.markdown(
    """
    <style>
        .block-container {
            max-width: 760px;
            padding-top: 2rem;
            padding-bottom: 5rem;
        }

        [data-testid="stChatMessage"] {
            border-radius: 16px;
            padding: 0.35rem 0.75rem;
        }

        [data-testid="stChatMessage"] p {
            line-height: 1.55;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("💬 Olly")
st.caption("Conversa curta, opinião forte e zero enrolação.")


def get_api_key() -> str:
    """Lê a chave pelo nome configurado nos Secrets do Streamlit."""
    try:
        return st.secrets["AQ.Ab8RN6JNmAhyGQWouny6QVOZJGv2XyAGedadiyYYp5ZMdXBXpw"]
    except Exception as exc:
        st.error(
            "Não encontrei a chave da API nos Secrets do Streamlit. "
            f"Configure o segredo com o nome `{SECRET_NAME}`."
        )
        st.stop()
        raise exc  # Apenas para satisfazer analisadores estáticos.


@st.cache_resource
def create_model(api_key: str):
    """Configura e reutiliza o modelo durante a sessão do app."""
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=SYSTEM_PROMPT,
        generation_config=genai.GenerationConfig(
            temperature=0.9,
            max_output_tokens=160,
        ),
    )


def to_gemini_history(messages: list[dict[str, str]]) -> list[dict]:
    """Converte o histórico do Streamlit para o formato da API do Gemini."""
    # A saudação inicial é apenas visual; a API espera que o histórico comece
    # por uma mensagem do usuário.
    if messages and messages[0]["role"] == "assistant":
        messages = messages[1:]

    return [
        {
            "role": "user" if message["role"] == "user" else "model",
            "parts": [message["content"]],
        }
        for message in messages
    ]


if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Oi. Eu sou a Olly. Manda a real — o que você quer resolver?",
        }
    ]


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


if prompt := st.chat_input("Converse com a Olly..."):
    previous_messages = st.session_state.messages.copy()
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Olly está pensando..."):
                model = create_model(get_api_key())
                chat = model.start_chat(
                    history=to_gemini_history(previous_messages)
                )
                response = chat.send_message(prompt)
                answer = response.text.strip()

            if not answer:
                answer = "Deu branco aqui. Tenta perguntar de outro jeito."

            st.markdown(answer)
            st.session_state.messages.append(
                {"role": "assistant", "content": answer}
            )
        except Exception as exc:
            error_message = (
                "Não consegui falar com o Gemini agora. "
                "Confere a chave e tenta de novo."
            )
            st.error(error_message)
            st.caption(f"Detalhe técnico: {exc}")

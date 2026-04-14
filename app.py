import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load env
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Load document
def load_document(file_path):
    try:
        with open(file_path, "r") as file:
            return file.read()
    except:
        return ""

# Get question
def get_question():
    return input("\nAsk your question (type 'exit' to quit): ")

# Generate answer
def get_answer(document, question):
    try:
        prompt = f"""
        Answer the question ONLY using the context below.
        If answer is not in context, say "Not found in document".

        Context:
        {document}

        Question:
        {question}
        """

        model = genai.GenerativeModel("models/gemini-2.5-flash")  # ✅ WORKING MODEL

        response = model.generate_content(prompt)

        return response.text

    except Exception as e:
        return f"❌ Error: {e}"

# for m in genai.list_models():
#     print(m.name)

# Main
def main():
    print("📄 AI Document Q&A System (Working Version)")

    document = load_document("data.txt")

    if not document:
        print("❌ No document found")
        return

    while True:
        question = get_question()

        if question.lower() == "exit":
            print("👋 Exiting...")
            break

        answer = get_answer(document, question)

        print("\n🤖 Answer:")
        print(answer)

if __name__ == "__main__":
    main()
class ChatService:

    def chat(self, user_id, message):

        history = memory.get(user_id)

        response = llm.generate(history)

        memory.add(user_id, "assistant", response)

        return response
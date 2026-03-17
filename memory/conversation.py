class ConversationMemory:
    def __init__(self):
        self.history = {}

    def get(self, user_id):
        return self.history.get(user_id, [])
        
    def add(self, user_id, role, content):
        
        if user_id not in self.history:
            self.history[user_id] = []

        self.history[user_id].append({
            "role": role,
            "content": content
        })  